/**
 * ASD预测系统 - 脑区热力图渲染模块
 * 
 * 功能：
 * 1. 基于AAL3脑区映射渲染激活热力图
 * 2. 支持交互式脑区高亮
 * 3. 显示脑区详细信息
 * 4. 颜色渐变映射（蓝->绿->黄->红）
 */

class BrainHeatmapRenderer {
    constructor(brainVisualizer) {
        this.visualizer = brainVisualizer;
        this.heatmapData = null;
        this.highlightedRegion = null;
        this.regionMarkers = [];
        
        // 颜色映射函数（蓝->绿->黄->红）
        this.colorMap = this.createColorMap();
        
        console.log('✅ BrainHeatmapRenderer 初始化完成');
    }

    /**
     * 创建颜色映射函数
     */
    createColorMap() {
        return function(value) {
            // value范围: 0-1
            let r, g, b;
            
            if (value < 0.25) {
                // 蓝 -> 绿
                const t = value / 0.25;
                r = 0;
                g = Math.floor(t * 255);
                b = Math.floor((1 - t) * 255);
            } else if (value < 0.5) {
                // 绿 -> 黄
                const t = (value - 0.25) / 0.25;
                r = Math.floor(t * 255);
                g = 255;
                b = 0;
            } else if (value < 0.75) {
                // 黄 -> 橙
                const t = (value - 0.5) / 0.25;
                r = 255;
                g = Math.floor((1 - t) * 255);
                b = 0;
            } else {
                // 橙 -> 红
                const t = (value - 0.75) / 0.25;
                r = 255;
                g = 0;
                b = Math.floor(t * 100);
            }
            
            return new THREE.Color(r / 255, g / 255, b / 255);
        };
    }

    /**
     * 应用脑区激活热力图
     * 
     * @param {Array} regionActivations - 脑区激活数据 [{regionId, activationLevel, name_cn}]
     * @param {Object} regionCentroids - 脑区质心坐标 {regionId: [x, y, z]}
     */
    async applyHeatmap(regionActivations, regionCentroids) {
        this.heatmapData = regionActivations;
        
        // 清除旧的标记
        this.clearMarkers();
        
        // 为每个激活脑区创建标记
        regionActivations.forEach(region => {
            const centroid = regionCentroids[region.regionId];
            if (centroid) {
                this.createRegionMarker(region, centroid);
            }
        });
        
        console.log(`🎨 热力图应用完成: ${regionActivations.length} 个脑区`);
    }

    /**
     * 创建脑区标记（发光球体）
     */
    createRegionMarker(region, centroid) {
        const activation = region.activationLevel;
        const color = this.colorMap(activation);
        
        // 创建球体几何体
        const radius = 3 + activation * 5; // 激活度越高，球体越大
        const geometry = new THREE.SphereGeometry(radius, 16, 16);
        
        // 创建发光材质
        const material = new THREE.MeshPhongMaterial({
            color: color,
            transparent: true,
            opacity: 0.7,
            emissive: color,
            emissiveIntensity: 0.5,
            shininess: 100
        });
        
        const marker = new THREE.Mesh(geometry, material);
        marker.position.set(centroid[0], centroid[1], centroid[2]);
        
        // 存储脑区信息
        marker.userData = {
            regionId: region.regionId,
            name: region.name_cn || region.name_en,
            activation: activation,
            originalScale: 1
        };
        
        this.visualizer.scene.add(marker);
        this.regionMarkers.push(marker);
    }

    /**
     * 清除所有标记
     */
    clearMarkers() {
        this.regionMarkers.forEach(marker => {
            this.visualizer.scene.remove(marker);
            marker.geometry.dispose();
            marker.material.dispose();
        });
        this.regionMarkers = [];
        this.highlightedRegion = null;
    }

    /**
     * 高亮指定脑区
     */
    highlightRegion(regionId) {
        // 重置之前的高亮
        if (this.highlightedRegion) {
            this.resetHighlight(this.highlightedRegion);
        }
        
        // 找到对应的标记
        const marker = this.regionMarkers.find(m => m.userData.regionId === regionId);
        if (marker) {
            // 放大并增加亮度
            marker.scale.set(1.5, 1.5, 1.5);
            marker.material.opacity = 1.0;
            marker.material.emissiveIntensity = 1.0;
            
            this.highlightedRegion = marker;
            
            // 显示信息面板
            this.showRegionInfo(marker.userData);
        }
    }

    /**
     * 重置高亮
     */
    resetHighlight(marker) {
        marker.scale.set(1, 1, 1);
        marker.material.opacity = 0.7;
        marker.material.emissiveIntensity = 0.5;
    }

    /**
     * 显示脑区信息面板
     */
    showRegionInfo(userData) {
        // 移除旧的信息面板
        const oldPanel = document.getElementById('region-info-panel');
        if (oldPanel) {
            oldPanel.remove();
        }
        
        // 创建新面板
        const panel = document.createElement('div');
        panel.id = 'region-info-panel';
        panel.style.cssText = `
            position: absolute;
            top: 20px;
            right: 20px;
            background: rgba(0, 0, 0, 0.85);
            color: white;
            padding: 20px;
            border-radius: 12px;
            min-width: 250px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            z-index: 1000;
        `;
        
        const activationPercent = (userData.activation * 100).toFixed(1);
        let activationLevel = '低';
        let levelColor = '#4a90e2';
        
        if (userData.activation > 0.7) {
            activationLevel = '非常高';
            levelColor = '#ff4444';
        } else if (userData.activation > 0.5) {
            activationLevel = '高';
            levelColor = '#ffaa00';
        } else if (userData.activation > 0.3) {
            activationLevel = '中等';
            levelColor = '#44ff44';
        }
        
        panel.innerHTML = `
            <h3 style="margin: 0 0 15px 0; color: #4a90e2;">🧠 脑区信息</h3>
            <div style="margin-bottom: 10px;">
                <strong>名称:</strong> ${userData.name}
            </div>
            <div style="margin-bottom: 10px;">
                <strong>AAL3 ID:</strong> ${userData.regionId}
            </div>
            <div style="margin-bottom: 10px;">
                <strong>激活水平:</strong> 
                <span style="color: ${levelColor}; font-weight: bold;">
                    ${activationLevel} (${activationPercent}%)
                </span>
            </div>
            <div style="margin-top: 15px; font-size: 12px; color: #aaa;">
                点击其他脑区查看详情
            </div>
        `;
        
        document.body.appendChild(panel);
    }

    /**
     * 清除信息面板
     */
    clearInfoPanel() {
        const panel = document.getElementById('region-info-panel');
        if (panel) {
            panel.remove();
        }
    }

    /**
     * 动画效果 - 脉动
     */
    animateMarkers(time) {
        this.regionMarkers.forEach((marker, index) => {
            const baseScale = 1 + Math.sin(time * 0.002 + index) * 0.1;
            if (marker !== this.highlightedRegion) {
                marker.scale.set(baseScale, baseScale, baseScale);
            }
        });
    }

    /**
     * 销毁
     */
    destroy() {
        this.clearMarkers();
        this.clearInfoPanel();
    }
}

// 导出类
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BrainHeatmapRenderer;
}
