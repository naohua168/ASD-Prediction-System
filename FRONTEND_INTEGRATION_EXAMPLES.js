/**
 * 前端调用示例 - 带预处理选项的分析任务
 * 
 * 将此代码集成到您的前端JavaScript中
 */

// ==========================================
// 示例1: 单个分析（启用预处理）
// ==========================================
async function startAnalysisWithPreprocessing(mriId, modelId = null) {
    const response = await fetch(`/analysis/start/${mriId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            model_id: modelId,              // 可选：指定模型ID
            use_preprocessing: true          // ✅ 启用预处理
        })
    });
    
    const data = await response.json();
    
    if (data.success) {
        console.log('✅ 任务已提交:', data.task_id);
        console.log('🔄 预处理已启用:', data.preprocessing_enabled);
        
        // 开始轮询任务状态
        pollTaskStatus(data.task_id);
    } else {
        console.error('❌ 提交失败:', data.error);
    }
}

// ==========================================
// 示例2: 单个分析（不使用预处理，默认行为）
// ==========================================
async function startAnalysisWithoutPreprocessing(mriId, modelId = null) {
    const response = await fetch(`/analysis/start/${mriId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            model_id: modelId,
            use_preprocessing: false  // ❌ 不启用预处理（默认）
        })
    });
    
    const data = await response.json();
    
    if (data.success) {
        console.log('✅ 任务已提交:', data.task_id);
        console.log('⚡ 使用原始文件（更快）');
        
        pollTaskStatus(data.task_id);
    }
}

// ==========================================
// 示例3: 批量分析（启用预处理）
// ==========================================
async function startBatchAnalysisWithPreprocessing(mriIds, modelId = null) {
    const response = await fetch('/analysis/start-batch', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            mri_ids: mriIds,                // MRI ID数组
            model_id: modelId,              // 可选：指定模型
            use_preprocessing: true          // ✅ 启用预处理
        })
    });
    
    const data = await response.json();
    
    if (data.success) {
        console.log(`✅ 批量提交完成: ${data.submitted}/${data.total}`);
        console.log('📊 任务列表:', data.task_ids);
        
        if (data.errors.length > 0) {
            console.warn('⚠️ 部分失败:', data.errors);
        }
        
        // 轮询所有任务状态
        data.task_ids.forEach(item => {
            pollTaskStatus(item.task_id);
        });
    }
}

// ==========================================
// 示例4: 让用户选择是否启用预处理
// ==========================================
function showAnalysisOptions(mriId) {
    // 显示确认对话框
    const usePreprocessing = confirm(
        '是否启用MRI预处理？\n\n' +
        '✅ 启用预处理（推荐）：\n' +
        '   • 头动校正、去颅骨、空间标准化\n' +
        '   • 提高分析准确性\n' +
        '   • 耗时约2-3秒\n\n' +
        '❌ 不启用预处理：\n' +
        '   • 直接使用原始文件\n' +
        '   • 速度更快\n' +
        '   • 适合已预处理的文件'
    );
    
    if (usePreprocessing) {
        startAnalysisWithPreprocessing(mriId);
    } else {
        startAnalysisWithoutPreprocessing(mriId);
    }
}

// ==========================================
// 工具函数：轮询任务状态
// ==========================================
function pollTaskStatus(taskId, interval = 2000) {
    const checkStatus = async () => {
        try {
            const response = await fetch(`/api/analysis/task-status/${taskId}`);
            const data = await response.json();
            
            console.log(`📊 任务 ${taskId}:`, {
                status: data.status,
                progress: data.progress + '%',
                message: data.message
            });
            
            if (data.status === 'completed') {
                console.log('✅ 分析完成！');
                console.log('📄 查看报告:', data.result_url);
                
                // 跳转到报告页面
                window.location.href = data.result_url;
                return;
            }
            
            if (data.status === 'failed') {
                console.error('❌ 分析失败:', data.error);
                alert('分析失败: ' + data.error);
                return;
            }
            
            if (data.status === 'cancelled') {
                console.warn('⚠️ 任务已取消');
                return;
            }
            
            // 继续轮询
            setTimeout(checkStatus, interval);
            
        } catch (error) {
            console.error('轮询失败:', error);
        }
    };
    
    checkStatus();
}

// ==========================================
// HTML 按钮示例
// ==========================================
/*
在您的HTML模板中添加：

<!-- 单个分析按钮 -->
<button onclick="showAnalysisOptions(123)" class="btn btn-primary">
    🧠 开始分析
</button>

<!-- 或者分别提供两个选项 -->
<div class="analysis-options">
    <button onclick="startAnalysisWithPreprocessing(123)" class="btn btn-success">
        ✅ 标准分析（含预处理）
    </button>
    
    <button onclick="startAnalysisWithoutPreprocessing(123)" class="btn btn-secondary">
        ⚡ 快速分析（跳过预处理）
    </button>
</div>

<!-- 批量分析 -->
<button onclick="startBatchAnalysisWithPreprocessing([1, 2, 3, 4, 5])" class="btn btn-primary">
    📊 批量分析（启用预处理）
</button>
*/

// ==========================================
// Vue.js 组件示例
// ==========================================
/*
<template>
  <div class="analysis-panel">
    <h3>MRI 分析</h3>
    
    <!-- 预处理选项 -->
    <div class="form-group">
      <label>
        <input type="checkbox" v-model="usePreprocessing" />
        启用MRI预处理（推荐）
      </label>
      <small class="text-muted">
        包括头动校正、去颅骨、空间标准化等步骤
      </small>
    </div>
    
    <!-- 模型选择 -->
    <div class="form-group">
      <label>选择模型：</label>
      <select v-model="selectedModel">
        <option value="">自动选择最佳模型</option>
        <option v-for="model in availableModels" :key="model.id" :value="model.id">
          {{ model.name }} (准确率: {{ (model.accuracy * 100).toFixed(1) }}%)
        </option>
      </select>
    </div>
    
    <!-- 分析按钮 -->
    <button 
      @click="startAnalysis" 
      :disabled="isAnalyzing"
      class="btn btn-primary"
    >
      {{ isAnalyzing ? '分析中...' : '开始分析' }}
    </button>
    
    <!-- 进度显示 -->
    <div v-if="isAnalyzing" class="progress-bar">
      <div 
        class="progress-fill" 
        :style="{ width: progress + '%' }"
      ></div>
      <span>{{ progress }}% - {{ statusMessage }}</span>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      usePreprocessing: true,
      selectedModel: '',
      isAnalyzing: false,
      progress: 0,
      statusMessage: '',
      availableModels: []
    };
  },
  
  methods: {
    async startAnalysis() {
      this.isAnalyzing = true;
      this.progress = 0;
      
      try {
        const response = await fetch(`/analysis/start/${this.mriId}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            model_id: this.selectedModel || null,
            use_preprocessing: this.usePreprocessing
          })
        });
        
        const data = await response.json();
        
        if (data.success) {
          this.pollTaskStatus(data.task_id);
        } else {
          throw new Error(data.error);
        }
      } catch (error) {
        console.error('启动分析失败:', error);
        alert('启动分析失败: ' + error.message);
        this.isAnalyzing = false;
      }
    },
    
    async pollTaskStatus(taskId) {
      const checkStatus = async () => {
        try {
          const response = await fetch(`/api/analysis/task-status/${taskId}`);
          const data = await response.json();
          
          this.progress = data.progress;
          this.statusMessage = data.message || data.status;
          
          if (data.status === 'completed') {
            this.isAnalyzing = false;
            window.location.href = data.result_url;
            return;
          }
          
          if (data.status === 'failed') {
            this.isAnalyzing = false;
            throw new Error(data.error);
          }
          
          setTimeout(checkStatus, 2000);
        } catch (error) {
          this.isAnalyzing = false;
          alert('分析失败: ' + error.message);
        }
      };
      
      checkStatus();
    },
    
    async loadAvailableModels() {
      try {
        const response = await fetch('/api/models/list');
        const data = await response.json();
        this.availableModels = data.models;
      } catch (error) {
        console.error('加载模型列表失败:', error);
      }
    }
  },
  
  mounted() {
    this.loadAvailableModels();
  }
};
</script>
*/

// ==========================================
// React 组件示例
// ==========================================
/*
import React, { useState, useEffect } from 'react';

function AnalysisPanel({ mriId }) {
  const [usePreprocessing, setUsePreprocessing] = useState(true);
  const [selectedModel, setSelectedModel] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState('');
  
  const startAnalysis = async () => {
    setIsAnalyzing(true);
    setProgress(0);
    
    try {
      const response = await fetch(`/analysis/start/${mriId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model_id: selectedModel || null,
          use_preprocessing: usePreprocessing
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        pollTaskStatus(data.task_id);
      } else {
        throw new Error(data.error);
      }
    } catch (error) {
      alert('启动分析失败: ' + error.message);
      setIsAnalyzing(false);
    }
  };
  
  const pollTaskStatus = (taskId) => {
    const checkStatus = async () => {
      const response = await fetch(`/api/analysis/task-status/${taskId}`);
      const data = await response.json();
      
      setProgress(data.progress);
      setStatusMessage(data.message || data.status);
      
      if (data.status === 'completed') {
        setIsAnalyzing(false);
        window.location.href = data.result_url;
        return;
      }
      
      if (data.status === 'failed') {
        setIsAnalyzing(false);
        alert('分析失败: ' + data.error);
        return;
      }
      
      setTimeout(checkStatus, 2000);
    };
    
    checkStatus();
  };
  
  return (
    <div className="analysis-panel">
      <h3>MRI 分析</h3>
      
      <div className="form-group">
        <label>
          <input
            type="checkbox"
            checked={usePreprocessing}
            onChange={(e) => setUsePreprocessing(e.target.checked)}
          />
          启用MRI预处理（推荐）
        </label>
      </div>
      
      <button
        onClick={startAnalysis}
        disabled={isAnalyzing}
        className="btn btn-primary"
      >
        {isAnalyzing ? `分析中... ${progress}%` : '开始分析'}
      </button>
      
      {isAnalyzing && (
        <div className="progress-bar">
          <div className="progress-fill" style={{ width: `${progress}%` }} />
          <span>{statusMessage}</span>
        </div>
      )}
    </div>
  );
}

export default AnalysisPanel;
*/

console.log('✅ 前端调用示例已加载');
console.log('💡 提示：根据您的前端框架选择合适的示例代码');
