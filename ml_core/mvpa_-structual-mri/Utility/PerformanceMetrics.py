from sklearn.metrics import f1_score,precision_score,confusion_matrix,recall_score,roc_auc_score

import numpy as np
class allMetrics:
    def __init__(self,**kwargs):
        self.metric={}
        for key, value in kwargs.items():
            self.metric[key]=[]
            self.metric[key].append(value)
    def printMetrics(self):
        print(self.metric)
    def mergeMetricList(self, mList):
        MetricList = allMetrics()
        for key in mList[0].metric.keys():
            MetricList.metric[key] = []
        for i in range(len(mList)):
            mc = mList[i]
            for key in mc.metric.keys():
                MetricList.metric[key].extend(mc.metric[key])
        return MetricList
    def getAverageMetric(self):
        avgMetric = allMetrics()
        for key in self.metric.keys():
            avgMetric.metric[key]=[]
            avgMetric.metric[key].append(np.mean(self.metric[key]))
        return avgMetric
    def getStdMetric(self):
        avgMetric = allMetrics()
        for key in self.metric.keys():
            avgMetric.metric[key]=[]
            avgMetric.metric[key].append(np.std(self.metric[key]))
        return avgMetric
    def getMaxMetric(self):
        avgMetric = allMetrics()
        id=self.metric["Accuracy_test"].index(max(self.metric["Accuracy_test"]))
        for key in self.metric.keys():
            avgMetric.metric[key]=[]
            avgMetric.metric[key].append(self.metric[key][id])
        return avgMetric,id

def SenSpe(TrueLabels, PredictLabels):
    cm = confusion_matrix(TrueLabels, PredictLabels)
    Sensitivity = cm[0, 0] / (cm[0, 0] + cm[0, 1])
    Specifity = cm[1, 1] / (cm[1, 0] + cm[1, 1])
    return Sensitivity,Specifity

def Metrics(TrueLabels, PredictLabels):
    F1 = f1_score(TrueLabels, PredictLabels)
    Precision = precision_score(TrueLabels,PredictLabels)
    Recall = recall_score(TrueLabels,PredictLabels)
    Auc = roc_auc_score(TrueLabels,PredictLabels)
    return F1,Precision,Recall,Auc
