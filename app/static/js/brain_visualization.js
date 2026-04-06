/**
 * ASD预测系统 - Three.js 3D脑部可视化模块（真实网格版）
 *
 * 功能：
 * 1. 加载真实NIfTI转换的3D网格
 * 2. 支持BufferGeometry高效渲染
 * 3. 基于预测结果的着色
 * 4. 交互式旋转、缩放、悬停
 */

class BrainVisualizer {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            throw new Error(`Container element '${containerId}' not found`);
        }

        this.options = {
            width: options.width || this.container.clientWidth || 800,
            height: options.height || this.container.clientHeight || 600,
            backgroundColor: options.backgroundColor || 0x0a0a1a,
            enableRotation: options.enableRotation !== false,
            autoRotateSpeed: options.autoRotateSpeed || 0.5,
            enableZoom: options.enableZoom !== false,
            meshUrl: options.meshUrl || null,
            analysisId: options.analysisId || null
        };

        // Three.js核心对象
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.raycaster = new THREE.Raycaster();
        this.mouse = new THREE.Vector2();

        // 脑部模型
        this.brainMesh = null;
        this.originalColors = null;

        // 交互状态
        this.isDragging = false;
        this.previousMousePosition = { x: 0, y: 0 };
        this.animationId = null;
        this.autoRotateEnabled = false;

        this.init();
    }

    init() {
        this.createScene();
        this.createCamera();
        this.createRenderer();
        this.createLights();
        this.addEventListeners();

        // 加载网格数据
        if (this.options.meshUrl) {
            this.loadMeshFromUrl(this.options.meshUrl);
        } else if (this.options.analysisId) {
            this.loadMeshFromAnalysis(this.options.analysisId);
        } else {
            this.loadDefaultBrain();
        }

        this.animate();
        console.log('✅ BrainVisualizer 初始化完成');
    }

    createScene() {
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(this.options.backgroundColor);
    }

    createCamera() {
        const aspect = this.options.width / this.options.height;
        this.camera = new THREE.PerspectiveCamera(60, aspect, 0.1, 1000);
        this.camera.position.set(0, 0, 150);
        this.camera.lookAt(0, 0, 0);
    }

    createRenderer() {
        this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        this.renderer.setSize(this.options.width, this.options.height);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.renderer.shadowMap.enabled = true;

        this.container.innerHTML = '';
        this.container.appendChild(this.renderer.domElement);
    }

    createLights() {
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
        this.scene.add(ambientLight);

        const mainLight = new THREE.DirectionalLight(0xffffff, 0.8);
        mainLight.position.set(50, 50, 50);
        mainLight.castShadow = true;
        this.scene.add(mainLight);

        const fillLight = new THREE.DirectionalLight(0x8888ff, 0.3);
        fillLight.position.set(-50, -50, -50);
        this.scene.add(fillLight);
    }

    /**
     * 从URL加载网格JSON
     */
    async loadMeshFromUrl(url) {
        try {
            console.log('📦 加载网格数据:', url);
            const response = await fetch(url);
            const meshData = await response.json();
            this.createBrainMesh(meshData);
        } catch (error) {
            console.error('❌ 加载网格失败:', error);
            this.showError('无法加载脑部模型');
        }
    }

    /**
     * 从分析结果ID加载网格
     */
    async loadMeshFromAnalysis(analysisId) {
        try {
            console.log('📦 从分析结果加载网格:', analysisId);
            const response = await fetch(`/api/analysis/${analysisId}/brain-mesh`);
            const data = await response.json();

            if (data.success && data.mesh_data) {
                this.createBrainMesh(data.mesh_data);

                // 根据预测结果着色
                if (data.prediction) {
                    this.applyPredictionColors(data.prediction, data.confidence);
                }
            } else {
                throw new Error(data.error || '获取网格数据失败');
            }
        } catch (error) {
            console.error('❌ 加载分析网格失败:', error);
            this.loadDefaultBrain();
        }
    }

    /**
     * 创建脑部网格
     * 支持两种格式：
     * 1. 新格式: {left_hemisphere: {coordinates, faces}, right_hemisphere: {...}}
     * 2. 旧格式: {vertices, faces, normals}
     */
    createBrainMesh(meshData) {
        // 检测数据格式
        if (meshData.left_hemisphere && meshData.right_hemisphere) {
            // 新格式：左右半球分开
            this.createDualHemisphereMesh(meshData);
        } else if (meshData.vertices && meshData.faces) {
            // 旧格式：单一网格
            this.createSingleMesh(meshData);
        } else {
            console.error('❌ 不支持的网格数据格式');
            this.loadDefaultBrain();
        }
    }

    /**
     * 创建双半球网格（新格式）
     */
    createDualHemisphereMesh(meshData) {
        const group = new THREE.Group();

        // 创建左侧半球
        if (meshData.left_hemisphere && meshData.left_hemisphere.coordinates.length > 0) {
            const leftMesh = this.createHemisphereMesh(
                meshData.left_hemisphere,
                0x4a90e2,  // 蓝色
                'left'
            );
            group.add(leftMesh);
        }

        // 创建右侧半球
        if (meshData.right_hemisphere && meshData.right_hemisphere.coordinates.length > 0) {
            const rightMesh = this.createHemisphereMesh(
                meshData.right_hemisphere,
                0x5ba3f5,  // 稍浅的蓝色
                'right'
            );
            group.add(rightMesh);
        }

        this.brainMesh = group;
        this.scene.add(this.brainMesh);

        // 保存原始颜色
        this.originalColors = {
            left: 0x4a90e2,
            right: 0x5ba3f5
        };

        const totalVertices = (meshData.left_hemisphere?.coordinates.length || 0) + 
                              (meshData.right_hemisphere?.coordinates.length || 0);
        const totalFaces = (meshData.left_hemisphere?.faces.length || 0) + 
                           (meshData.right_hemisphere?.faces.length || 0);
        console.log(`🧠 双半球网格创建完成: ${totalVertices / 3} 顶点, ${totalFaces / 3} 面`);
    }

    /**
     * 创建单个半球的网格
     */
    createHemisphereMesh(hemisphereData, color, side) {
        const geometry = new THREE.BufferGeometry();

        // 设置顶点坐标
        const coords = hemisphereData.coordinates;
        const verticesArray = new Float32Array(coords.flat());
        geometry.setAttribute('position', new THREE.BufferAttribute(verticesArray, 3));

        // 设置面片索引
        const faces = hemisphereData.faces;
        const facesArray = new Uint32Array(faces.flat());
        geometry.setIndex(new THREE.BufferAttribute(facesArray, 1));

        // 计算法线
        geometry.computeVertexNormals();

        // 创建材质
        const material = new THREE.MeshPhongMaterial({
            color: color,
            transparent: true,
            opacity: 0.85,
            shininess: 60,
            specular: 0x444444,
            side: THREE.DoubleSide,
            flatShading: false
        });

        const mesh = new THREE.Mesh(geometry, material);
        mesh.name = `${side}_hemisphere`;

        return mesh;
    }

    /**
     * 创建单一网格（旧格式兼容）
     */
    createSingleMesh(meshData) {
        const { vertices, faces, normals } = meshData;

        // 创建BufferGeometry
        const geometry = new THREE.BufferGeometry();

        // 设置顶点
        const verticesArray = new Float32Array(vertices);
        geometry.setAttribute('position', new THREE.BufferAttribute(verticesArray, 3));

        // 设置法线
        if (normals && normals.length > 0) {
            const normalsArray = new Float32Array(normals);
            geometry.setAttribute('normal', new THREE.BufferAttribute(normalsArray, 3));
        } else {
            geometry.computeVertexNormals();
        }

        // 设置索引（面）
        const facesArray = new Uint32Array(faces);
        geometry.setIndex(new THREE.BufferAttribute(facesArray, 1));

        // 创建材质
        const material = new THREE.MeshPhongMaterial({
            color: 0x4a90e2,
            transparent: true,
            opacity: 0.85,
            shininess: 60,
            specular: 0x444444,
            side: THREE.DoubleSide,
            flatShading: false
        });

        // 创建网格
        this.brainMesh = new THREE.Mesh(geometry, material);
        this.scene.add(this.brainMesh);

        // 保存原始颜色
        this.originalColors = {
            r: material.color.r,
            g: material.color.g,
            b: material.color.b
        };

        console.log(`🧠 单网格创建完成: ${vertices.length / 3} 顶点, ${faces.length / 3} 面`);
    }

    /**
     * 应用预测结果的颜色
     */
    applyPredictionColors(prediction, confidence) {
        if (!this.brainMesh) return;

        // 确定目标颜色
        let targetColor;
        if (prediction === 'ASD') {
            // ASD: 红色调
            const intensity = confidence || 0.8;
            targetColor = new THREE.Color(0.9, 0.3 + (1 - intensity) * 0.3, 0.3);
        } else {
            // NC: 蓝绿色调
            const intensity = confidence || 0.8;
            targetColor = new THREE.Color(0.2, 0.7 + intensity * 0.2, 0.6);
        }

        // 检查是否为双半球网格
        if (this.brainMesh.type === 'Group') {
            // 双半球：为每个半球设置颜色
            this.brainMesh.children.forEach((mesh, index) => {
                if (mesh.material) {
                    mesh.material.color.copy(targetColor);
                }
            });
            console.log(`🎨 应用预测颜色到双半球: ${prediction} (置信度: ${(confidence * 100).toFixed(1)}%)`);
        } else {
            // 单网格：直接设置颜色
            const material = this.brainMesh.material;
            material.color.copy(targetColor);
            console.log(`🎨 应用预测颜色: ${prediction} (置信度: ${(confidence * 100).toFixed(1)}%)`);
        }
    }

    /**
     * 加载默认脑部（备用）
     */
    loadDefaultBrain() {
        console.log('⚠️  使用默认球体模型');

        const geometry = new THREE.SphereGeometry(50, 64, 64);
        const material = new THREE.MeshPhongMaterial({
            color: 0x4a90e2,
            transparent: true,
            opacity: 0.8,
            shininess: 50
        });

        this.brainMesh = new THREE.Mesh(geometry, material);
        this.scene.add(this.brainMesh);
    }

    addEventListeners() {
        // 鼠标移动
        this.renderer.domElement.addEventListener('mousemove', (event) => {
            this.onMouseMove(event);
        });

        // 窗口调整
        window.addEventListener('resize', () => {
            this.onWindowResize();
        });

        // 滚轮缩放
        if (this.options.enableZoom) {
            this.renderer.domElement.addEventListener('wheel', (event) => {
                this.onWheel(event);
            });
        }

        // 拖拽旋转
        if (this.options.enableRotation) {
            this.renderer.domElement.addEventListener('mousedown', (event) => {
                this.isDragging = true;
                this.previousMousePosition = { x: event.clientX, y: event.clientY };
            });

            this.renderer.domElement.addEventListener('mouseup', () => {
                this.isDragging = false;
            });

            this.renderer.domElement.addEventListener('mouseleave', () => {
                this.isDragging = false;
            });

            this.renderer.domElement.addEventListener('mousemove', (event) => {
                if (this.isDragging) {
                    this.onDrag(event);
                }
            });
        }
    }

    onMouseMove(event) {
        const rect = this.renderer.domElement.getBoundingClientRect();
        this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
    }

    onDrag(event) {
        const deltaMove = {
            x: event.clientX - this.previousMousePosition.x,
            y: event.clientY - this.previousMousePosition.y
        };

        const rotateSpeed = 0.005;
        this.brainMesh.rotation.y += deltaMove.x * rotateSpeed;
        this.brainMesh.rotation.x += deltaMove.y * rotateSpeed;

        this.previousMousePosition = { x: event.clientX, y: event.clientY };
    }

    onWheel(event) {
        event.preventDefault();
        const zoomSpeed = 0.05;
        const delta = event.deltaY > 0 ? 1 + zoomSpeed : 1 - zoomSpeed;
        this.camera.position.z *= delta;
        this.camera.position.z = Math.max(50, Math.min(300, this.camera.position.z));
    }

    onWindowResize() {
        this.options.width = this.container.clientWidth;
        this.options.height = this.container.clientHeight;
        this.camera.aspect = this.options.width / this.options.height;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(this.options.width, this.options.height);
    }

    resetView() {
        this.camera.position.set(0, 0, 150);
        this.camera.lookAt(0, 0, 0);
        if (this.brainMesh) {
            this.brainMesh.rotation.set(0, 0, 0);
        }
    }

    toggleAutoRotate(enabled) {
        this.autoRotateEnabled = enabled;
    }

    animate() {
        this.animationId = requestAnimationFrame(() => this.animate());

        if (this.autoRotateEnabled && !this.isDragging && this.brainMesh) {
            this.brainMesh.rotation.y += 0.002 * this.options.autoRotateSpeed;
        }

        this.renderer.render(this.scene, this.camera);
    }

    destroy() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
        this.renderer.dispose();
        this.scene.clear();
        if (this.container) {
            this.container.innerHTML = '';
        }
    }

    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.style.cssText = `
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(255, 0, 0, 0.1);
            border: 2px solid red;
            color: red;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        `;
        errorDiv.textContent = message;
        this.container.appendChild(errorDiv);
    }
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = BrainVisualizer;
}
