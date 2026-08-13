// Three.js 3D Background with Animated Particles
let scene, camera, renderer, particles, particleSystem;
let mouseX = 0, mouseY = 0;

function initThreeBackground() {
    // Create scene
    scene = new THREE.Scene();
    
    // Camera setup
    camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.z = 50;
    
    // Renderer setup
    renderer = new THREE.WebGLRenderer({ 
        alpha: true,
        antialias: true 
    });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    
    // Add canvas to page
    const canvas = renderer.domElement;
    canvas.style.position = 'fixed';
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.style.zIndex = '-1';
    canvas.style.pointerEvents = 'none';
    canvas.style.opacity = '0.58';
    document.body.insertBefore(canvas, document.body.firstChild);
    
    // Create particles
    const particleCount = 1500;
    const particles = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);
    const sizes = new Float32Array(particleCount);
    
    const colorPalette = [
        new THREE.Color(0x0a58ca), // Medium blue
        new THREE.Color(0x5518c8), // Medium purple
        new THREE.Color(0x0aa0c0), // Medium cyan
        new THREE.Color(0x18a070), // Medium teal
        new THREE.Color(0xc89810), // Medium gold
    ];
    
    for (let i = 0; i < particleCount * 3; i += 3) {
        // Position
        positions[i] = (Math.random() - 0.5) * 200;
        positions[i + 1] = (Math.random() - 0.5) * 200;
        positions[i + 2] = (Math.random() - 0.5) * 200;
        
        // Color
        const color = colorPalette[Math.floor(Math.random() * colorPalette.length)];
        colors[i] = color.r;
        colors[i + 1] = color.g;
        colors[i + 2] = color.b;
        
        // Size
        sizes[i / 3] = Math.random() * 1.6 + 0.4;
    }
    
    particles.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    particles.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    particles.setAttribute('size', new THREE.BufferAttribute(sizes, 1));
    
    // Particle material
    const particleMaterial = new THREE.PointsMaterial({
        size: 1.7,
        vertexColors: true,
        transparent: true,
        opacity: 0.62,
        blending: THREE.NormalBlending,
        sizeAttenuation: true
    });
    
    particleSystem = new THREE.Points(particles, particleMaterial);
    scene.add(particleSystem);
    
    // Mouse move listener for parallax
    document.addEventListener('mousemove', (event) => {
        mouseX = (event.clientX / window.innerWidth) * 2 - 1;
        mouseY = -(event.clientY / window.innerHeight) * 2 + 1;
    });
    
    // Window resize handler
    window.addEventListener('resize', onWindowResize, false);
    
    // Start animation
    animate();
}

function onWindowResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
}

function animate() {
    requestAnimationFrame(animate);
    
    // Rotate particle system
    particleSystem.rotation.y += 0.001;
    particleSystem.rotation.x += 0.0005;
    
    // Parallax effect based on mouse position
    camera.position.x += (mouseX * 3.5 - camera.position.x) * 0.04;
    camera.position.y += (mouseY * 3.5 - camera.position.y) * 0.04;
    camera.lookAt(scene.position);
    
    // Animate particles
    const positions = particleSystem.geometry.attributes.position.array;
    for (let i = 0; i < positions.length; i += 3) {
        positions[i + 1] += Math.sin(Date.now() * 0.001 + i) * 0.01;
    }
    particleSystem.geometry.attributes.position.needsUpdate = true;
    
    renderer.render(scene, camera);
}

// Initialize when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initThreeBackground);
} else {
    initThreeBackground();
}
