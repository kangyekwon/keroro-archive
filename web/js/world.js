/* === Keroro Archive - Three.js 3D World === */

var worldScene, worldCamera, worldRenderer, worldAnimId;

async function initWorld() {
    var container = document.getElementById('world-container');
    var overlay = document.getElementById('world-overlay');

    try {
        var data = await api('/api/world');
        var groups = data.groups || data.locations || [];

        var w = container.clientWidth || 800;
        var h = container.clientHeight || 600;

        // Scene setup
        worldScene = new THREE.Scene();
        worldScene.fog = new THREE.FogExp2(0x0d1117, 0.035);

        // Camera
        worldCamera = new THREE.PerspectiveCamera(60, w / h, 0.1, 1000);
        worldCamera.position.set(0, 5, 20);
        worldCamera.lookAt(0, 0, 0);

        // Renderer
        worldRenderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        worldRenderer.setSize(w, h);
        worldRenderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        worldRenderer.setClearColor(0x0d1117);
        container.appendChild(worldRenderer.domElement);

        if (overlay) overlay.style.display = 'none';

        // Lighting - Military green themed
        worldScene.add(new THREE.AmbientLight(0x223322, 0.5));
        var pointLight1 = new THREE.PointLight(0x4a7c59, 1.2, 60);
        pointLight1.position.set(5, 10, 10);
        worldScene.add(pointLight1);
        var pointLight2 = new THREE.PointLight(0xffd700, 0.6, 40);
        pointLight2.position.set(-5, 8, -5);
        worldScene.add(pointLight2);

        // Central planet sphere (Keron Star / Earth)
        var planetGeo = new THREE.SphereGeometry(3, 32, 32);
        var planetMat = new THREE.MeshPhongMaterial({
            color: 0x4a7c59,
            emissive: 0x1a2e1a,
            transparent: true,
            opacity: 0.6,
            wireframe: false
        });
        var planet = new THREE.Mesh(planetGeo, planetMat);
        worldScene.add(planet);

        // Wireframe overlay
        var wireGeo = new THREE.IcosahedronGeometry(3.2, 2);
        var wireMat = new THREE.MeshBasicMaterial({
            color: 0x4a7c59, wireframe: true, transparent: true, opacity: 0.15
        });
        var wireSphere = new THREE.Mesh(wireGeo, wireMat);
        worldScene.add(wireSphere);

        // Orbital rings
        var ringColors = [0x4a7c59, 0xffd700, 0x4fc3f7];
        var rings = [];
        for (var ri = 0; ri < 3; ri++) {
            var ringGeo = new THREE.TorusGeometry(4.5 + ri * 1.2, 0.02, 8, 64);
            var ringMat = new THREE.MeshBasicMaterial({
                color: ringColors[ri], transparent: true, opacity: 0.2
            });
            var ring = new THREE.Mesh(ringGeo, ringMat);
            ring.rotation.x = Math.PI / 2 + ri * 0.4;
            ring.rotation.y = ri * 0.6;
            rings.push(ring);
            worldScene.add(ring);
        }

        // Character group spheres
        var GROUP_COLORS = {
            '케로로소대': 0x4a7c59,
            '가루루소대': 0x6633cc,
            '히나타가': 0xff9f43,
            '인간': 0xff9f43,
            '케론인': 0x4a7c59,
            '기타': 0xa29bfe
        };

        var groupSprites = [];
        var groupAngle = 0;
        var groupRadius = 7;

        groups.forEach(function(group, gi) {
            var groupName = group.name || group.group || ('그룹 ' + (gi + 1));
            var members = group.members || group.characters || [];
            var groupColor = GROUP_COLORS[groupName] || 0x888888;

            // Group center position (distributed around orbit)
            var angle = (gi / Math.max(groups.length, 1)) * Math.PI * 2;
            var gx = Math.cos(angle) * groupRadius;
            var gz = Math.sin(angle) * groupRadius;
            var gy = Math.sin(angle * 2) * 1.5;

            // Group marker sphere
            var markerGeo = new THREE.SphereGeometry(0.5, 16, 16);
            var markerMat = new THREE.MeshBasicMaterial({
                color: groupColor, transparent: true, opacity: 0.8
            });
            var marker = new THREE.Mesh(markerGeo, markerMat);
            marker.position.set(gx, gy, gz);
            marker.userData = { groupName: groupName, members: members };
            worldScene.add(marker);

            // Glow for group marker
            var glowGeo = new THREE.SphereGeometry(0.8, 16, 16);
            var glowMat = new THREE.MeshBasicMaterial({
                color: groupColor, transparent: true, opacity: 0.15
            });
            var glow = new THREE.Mesh(glowGeo, glowMat);
            glow.position.copy(marker.position);
            worldScene.add(glow);

            // Group label sprite
            var labelCanvas = document.createElement('canvas');
            labelCanvas.width = 512;
            labelCanvas.height = 128;
            var ctx = labelCanvas.getContext('2d');
            ctx.font = 'bold 32px "Malgun Gothic", "Apple SD Gothic Neo", "Noto Sans KR", sans-serif';
            var textW = ctx.measureText(groupName).width;
            var pillW = textW + 40;
            var pillH = 48;
            var pillX = (512 - pillW) / 2;
            var pillY = 40;
            ctx.fillStyle = 'rgba(13,17,23,0.85)';
            ctx.beginPath();
            ctx.rect(pillX, pillY, pillW, pillH);
            ctx.fill();
            var hexColor = '#' + groupColor.toString(16).padStart(6, '0');
            ctx.strokeStyle = hexColor;
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.rect(pillX, pillY, pillW, pillH);
            ctx.stroke();
            ctx.fillStyle = hexColor;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(groupName, 256, pillY + pillH / 2);

            var labelTexture = new THREE.CanvasTexture(labelCanvas);
            var labelSpriteMat = new THREE.SpriteMaterial({
                map: labelTexture, transparent: true, opacity: 0.9, depthTest: false
            });
            var labelSprite = new THREE.Sprite(labelSpriteMat);
            labelSprite.position.set(gx, gy + 1.2, gz);
            labelSprite.scale.set(3.5, 0.85, 1);
            labelSprite.renderOrder = 999;
            worldScene.add(labelSprite);

            // Member spheres orbiting the group
            members.forEach(function(member, mi) {
                var memberName = member.name || member;
                var memberAngle = (mi / Math.max(members.length, 1)) * Math.PI * 2;
                var mr = 1.5 + mi * 0.3;
                var mx = gx + Math.cos(memberAngle) * mr;
                var mz = gz + Math.sin(memberAngle) * mr;
                var my = gy + Math.sin(memberAngle * 3) * 0.5;

                var MEMBER_COLORS = {
                    '케로로': 0x4a7c59,
                    '기로로': 0xcc3333,
                    '타마마': 0x3366cc,
                    '쿠루루': 0xffd700,
                    '도로로': 0x66bbee,
                    '가루루': 0x6633cc,
                    '나츠미': 0xff9f43,
                    '후유키': 0x88aa88,
                    '모모카': 0xfd79a8
                };

                var mColor = MEMBER_COLORS[memberName] || groupColor;
                var mGeo = new THREE.SphereGeometry(0.25, 12, 12);
                var mMat = new THREE.MeshBasicMaterial({
                    color: mColor, transparent: true, opacity: 0.9
                });
                var mMesh = new THREE.Mesh(mGeo, mMat);
                mMesh.position.set(mx, my, mz);
                mMesh.userData = {
                    memberName: memberName,
                    floatBase: my,
                    floatSpeed: 0.5 + Math.random() * 0.5,
                    floatAmp: 0.15 + Math.random() * 0.1,
                    orbitCenter: { x: gx, z: gz },
                    orbitRadius: mr,
                    orbitAngle: memberAngle,
                    orbitSpeed: 0.003 + Math.random() * 0.003
                };
                worldScene.add(mMesh);
                groupSprites.push(mMesh);
            });
        });

        // Background stars
        var starsGeo = new THREE.BufferGeometry();
        var starsCount = 2500;
        var starsPos = new Float32Array(starsCount * 3);
        var starsColors = new Float32Array(starsCount * 3);
        for (var j = 0; j < starsCount; j++) {
            starsPos[j * 3] = (Math.random() - 0.5) * 150;
            starsPos[j * 3 + 1] = (Math.random() - 0.5) * 150;
            starsPos[j * 3 + 2] = (Math.random() - 0.5) * 150;
            var brightness = 0.4 + Math.random() * 0.6;
            starsColors[j * 3] = brightness;
            starsColors[j * 3 + 1] = brightness;
            starsColors[j * 3 + 2] = brightness + Math.random() * 0.15;
        }
        starsGeo.setAttribute('position', new THREE.BufferAttribute(starsPos, 3));
        starsGeo.setAttribute('color', new THREE.BufferAttribute(starsColors, 3));
        worldScene.add(new THREE.Points(starsGeo, new THREE.PointsMaterial({
            size: 0.06, vertexColors: true, transparent: true, opacity: 0.7,
            blending: THREE.AdditiveBlending, depthWrite: false
        })));

        // Green particle dust
        var dustGeo = new THREE.BufferGeometry();
        var dustCount = 500;
        var dustPos = new Float32Array(dustCount * 3);
        for (var di = 0; di < dustCount; di++) {
            var phi = Math.acos(2 * Math.random() - 1);
            var theta = Math.random() * Math.PI * 2;
            var dr = 3.5 + Math.random() * 1;
            dustPos[di * 3] = dr * Math.sin(phi) * Math.cos(theta);
            dustPos[di * 3 + 1] = dr * Math.sin(phi) * Math.sin(theta);
            dustPos[di * 3 + 2] = dr * Math.cos(phi);
        }
        dustGeo.setAttribute('position', new THREE.BufferAttribute(dustPos, 3));
        var dustParticles = new THREE.Points(dustGeo, new THREE.PointsMaterial({
            size: 0.05, color: 0x4a7c59, transparent: true,
            opacity: 0.6, blending: THREE.AdditiveBlending, depthWrite: false
        }));
        worldScene.add(dustParticles);

        // Mouse interaction
        var mouseX = 0, mouseY = 0;
        var targetCam = null;
        container.addEventListener('mousemove', function(e) {
            var rect = container.getBoundingClientRect();
            mouseX = ((e.clientX - rect.left) / w - 0.5) * 2;
            mouseY = ((e.clientY - rect.top) / h - 0.5) * 2;
        });
        container.addEventListener('wheel', function(e) {
            e.preventDefault();
            worldCamera.position.z += e.deltaY * 0.01;
            worldCamera.position.z = Math.max(10, Math.min(35, worldCamera.position.z));
        }, { passive: false });

        // Click tooltip
        var tooltip = document.createElement('div');
        tooltip.className = 'world-tooltip';
        tooltip.style.display = 'none';
        container.appendChild(tooltip);

        var raycaster = new THREE.Raycaster();
        var mouseVec = new THREE.Vector2();

        container.addEventListener('click', function(e) {
            var rect = container.getBoundingClientRect();
            mouseVec.x = ((e.clientX - rect.left) / w) * 2 - 1;
            mouseVec.y = -((e.clientY - rect.top) / h) * 2 + 1;
            raycaster.setFromCamera(mouseVec, worldCamera);
            var intersects = raycaster.intersectObjects(groupSprites);
            if (intersects.length > 0) {
                var hit = intersects[0].object;
                if (hit.userData && hit.userData.memberName) {
                    tooltip.textContent = hit.userData.memberName;
                    tooltip.style.display = 'block';
                    tooltip.style.left = (e.clientX - rect.left + 10) + 'px';
                    tooltip.style.top = (e.clientY - rect.top - 30) + 'px';
                    setTimeout(function() { tooltip.style.display = 'none'; }, 3000);
                }
            }
        });

        // Reset button
        var resetBtn = document.getElementById('world-reset');
        if (resetBtn) {
            resetBtn.addEventListener('click', function() {
                targetCam = { x: 0, y: 5, z: 20 };
            });
        }

        // Animation loop
        var time = 0;
        function animate() {
            worldAnimId = requestAnimationFrame(animate);
            time += 0.005;

            // Rotate planet
            planet.rotation.y += 0.001;
            wireSphere.rotation.y += 0.0008;
            dustParticles.rotation.y += 0.0005;

            // Rotate rings
            rings.forEach(function(ring, idx) {
                ring.rotation.z += 0.001 + idx * 0.0005;
            });

            // Orbit member spheres
            groupSprites.forEach(function(sprite) {
                var ud = sprite.userData;
                if (ud.orbitAngle !== undefined) {
                    ud.orbitAngle += ud.orbitSpeed;
                    sprite.position.x = ud.orbitCenter.x + Math.cos(ud.orbitAngle) * ud.orbitRadius;
                    sprite.position.z = ud.orbitCenter.z + Math.sin(ud.orbitAngle) * ud.orbitRadius;
                    sprite.position.y = ud.floatBase + Math.sin(time * ud.floatSpeed * 3) * ud.floatAmp;
                }
            });

            // Camera follow mouse or animate to target
            if (targetCam) {
                worldCamera.position.x += (targetCam.x - worldCamera.position.x) * 0.03;
                worldCamera.position.y += (targetCam.y - worldCamera.position.y) * 0.03;
                worldCamera.position.z += (targetCam.z - worldCamera.position.z) * 0.03;
                if (Math.abs(worldCamera.position.x - targetCam.x) < 0.05 &&
                    Math.abs(worldCamera.position.y - targetCam.y) < 0.05 &&
                    Math.abs(worldCamera.position.z - targetCam.z) < 0.05) {
                    targetCam = null;
                }
            } else {
                worldCamera.position.x += (mouseX * 3 - worldCamera.position.x) * 0.02;
                worldCamera.position.y += (-mouseY * 2 + 5 - worldCamera.position.y) * 0.02;
            }
            worldCamera.lookAt(0, 0, 0);

            // Pulse lights
            pointLight1.intensity = 1.0 + Math.sin(time * 2) * 0.3;
            pointLight2.intensity = 0.5 + Math.sin(time * 1.5 + 1) * 0.2;

            worldRenderer.render(worldScene, worldCamera);
        }
        animate();

        // Resize
        window.addEventListener('resize', function() {
            var nw = container.clientWidth, nh = container.clientHeight;
            if (nw && nh) {
                w = nw; h = nh;
                worldCamera.aspect = nw / nh;
                worldCamera.updateProjectionMatrix();
                worldRenderer.setSize(nw, nh);
            }
        });

    } catch (e) {
        if (overlay) overlay.innerHTML = '<p style="color:var(--danger);padding:2rem;">3D World Load Failed: ' + e.message + '</p>';
    }
}
