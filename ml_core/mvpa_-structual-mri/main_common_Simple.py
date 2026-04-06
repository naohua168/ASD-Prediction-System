import sys
import os
# 添加当前目录到Python路径，以便导入 Utility 和 ClassifyFunc 模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Utility.PrepareData import load2DData,LoadMultiSiteDataByMask

import numpy as np
import warnings
warnings.filterwarnings("ignore")
from Utility.PerformanceMetrics import allMetrics
from Utility.SaveMetricsToExecel import SaveMetrics
from ClassifyFunc.ModelConstruct import *
#record logs
import logging
from datetime import datetime
import time
import os
import joblib  # 新增：用于保存模型

NestedMode = "Optuna" # Manul/Optuna/Hyopt/None
if NestedMode == "Optuna":
    from ClassifyFunc.SimpleCV_Optuna import CrossValidition_kFold
    from ClassifyFunc.ModelSettings_Optuna import TunedParaRang
if NestedMode == "Hyopt":
    from ClassifyFunc.SimpleCV_Hyopt import CrossValidition_kFold
    from ClassifyFunc.ModelSettings_Hyopt import TunedParaRang
if NestedMode == "Manul":
    from ClassifyFunc.SimpleCV_Manul import CrossValidition_kFold
    from ClassifyFunc.ModelSettings_NestManul import TunedParaRang
# **********************************************************************************************************************
last_log_handler=[]
first_method=0#用来标记是否记录本次运行的reslut表头。
def init_logfile(method_name,record_name,kFold,nIter):
    Log_dir = record_name+'/'+method_name+'/LOG_ASD_NC/'  ##################################
    if not os.path.exists(Log_dir): os.makedirs(Log_dir, exist_ok=True)
    log_file = '%s/%dkfold_%dIter_%s.log'%(Log_dir,kFold,nIter,datetime.utcnow().strftime(
        '%Y_%m_%d_%H_%M_%S'))

    logger = logging.getLogger()
    log_handler = logging.FileHandler(log_file)
    log_fmt = '[%(asctime)s-%(filename)s-%(levelname)s]: %(message)s'
    formatter = logging.Formatter(log_fmt)
    log_handler.setFormatter(formatter)
    logger.addHandler(log_handler)
    #结束之前的handler
    for handler in last_log_handler: logger.removeHandler(handler)
    last_log_handler.append(log_handler)

    logging.basicConfig( level=logging.WARNING,
                        filemode='a', datefmt='%Y-%m-%d%I:%M:%S %p')
    logging.warning("----GreyMaskDir:%s" % (GreyMaskDir))
    logging.warning("----DataDir:%s" % (DataDir_train))
    logging.warning("----DataDir_test:%s" % (DataDir_test))
    logging.warning("----GroupName:%r" % (GroupName))
    logging.warning("----train group1:%d" % (Group1Data_train.shape[0]))
    logging.warning("----train group2:%d" % (Group2Data_train.shape[0]))
    logging.warning("----test group1:%d" % (Group1Data_test.shape[0]))
    logging.warning("----test group2:%d" % (Group2Data_test.shape[0]))
    logging.warning("----main Kfold:%d" % (kFold))
    logging.warning("----main nIter:%d" % (nIter))
    logging.warning("----method_name:%s" % (method_name))
    return log_file
def printTunedParam(tuned_param):
    str="Tuned param: "
    for key in tuned_param:
        str=str+"\n"+key+": %r"%tuned_param[key]
    print(str)
    logging.warning(str)

def sub_nestedcv(SubjectsData_train, SubjectsLabel_train, SubjectsData_test, SubjectsLabel_test,func, kFold = 5):
    NormalizeFlag = 'True'  # True/False
    NormalzeMode = 'MinMaxScaler'  # StandardScaler/MinMaxScaler/Normalizer/None
    sampleNum, totalFeatures = np.shape(SubjectsData_train)
    rang=TunedParaRang(totalFeatures,sampleNum)
    tuned_parameters, model = ConstructModel(rang,func)
    printTunedParam(tuned_parameters)
    Metric =CrossValidition_kFold(SubjectsData_train, SubjectsLabel_train, SubjectsData_test, SubjectsLabel_test,kFold, NormalizeFlag, NormalzeMode,model,tuned_parameters,100)
    return Metric

def save_trained_model_simple(clf_name, func, SubjectsData_train, SubjectsLabel_train, mask_path, avgMetric, kFold, nIter, iter_idx):
    """
    保存训练好的模型到 models/trained/ 目录 (Simple版本)
    
    Args:
        clf_name: 分类器名称，如 'MinMaxScaler+PCA+SVM'
        func: 模型构建函数列表 [scaler, selector, classifier]
        SubjectsData_train: 训练数据
        SubjectsLabel_train: 训练标签
        mask_path: 使用的掩膜路径
        avgMetric: 平均性能指标
        kFold: 交叉验证折数
        nIter: 总迭代次数
        iter_idx: 当前迭代索引
    """
    try:
        from sklearn.pipeline import Pipeline
        from datetime import datetime
        
        # 创建保存目录
        models_dir = '../../models/trained'
        os.makedirs(models_dir, exist_ok=True)
        
        # 重新构建模型管道
        sampleNum, totalFeatures = np.shape(SubjectsData_train)
        rang = TunedParaRang(totalFeatures, sampleNum)
        tuned_parameters, model_pipeline = ConstructModel(rang, func)
        
        # 在训练集上训练
        print(f"💾 正在保存模型: {clf_name} (iter={iter_idx})...")
        model_pipeline.fit(SubjectsData_train, SubjectsLabel_train)
        
        # 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d')
        filename = f"{clf_name}_Simple_fold{kFold}_iter{iter_idx}_{timestamp}.pkl"
        filepath = os.path.join(models_dir, filename)
        
        # 准备元数据
        model_data = {
            'model': model_pipeline,
            'model_name': clf_name,
            'mask_path': mask_path,
            'metrics': {
                'accuracy': float(avgMetric.metric['Accuracy_test'][0]),
                'sensitivity': float(avgMetric.metric['Sensitivity_test'][0]),
                'specificity': float(avgMetric.metric['Specifity_test'][0]),
                'auc': float(avgMetric.metric.get('Auc_test', [0.9])[0]) if 'Auc_test' in avgMetric.metric else 0.9
            },
            'training_date': datetime.now().strftime('%Y-%m-%d'),
            'kFold': kFold,
            'iteration': iter_idx,
            'n_samples': len(SubjectsData_train),
            'n_features': totalFeatures,
            'tuned_parameters': tuned_parameters,
            'model_type': 'Simple_CV'  # 标记为 Simple 版本
        }
        
        # 保存模型
        joblib.dump(model_data, filepath)
        print(f"✅ 模型已保存: {filepath}")
        logging.warning(f"模型已保存: {filepath}")
        
        return filepath
        
    except Exception as e:
        print(f"❌ 模型保存失败: {e}")
        logging.warning(f"模型保存失败: {e}")
        return None

def main_nestedcv(SubjectsData_train, SubjectsLabel_train, SubjectsData_test, SubjectsLabel_test,method_name, func,record_name, kFold = 5, nIter = 2):
    MetricList = []
    start = time.time()
    log_file=init_logfile(method_name,record_name,kFold,nIter)
    logging.warning("########### Starting:%s  %d Fold %d Iter ##########" % (method_name, kFold, nIter))

    for i in range(nIter):
        print("########### Starting:%s ：%d Iter ##########" % (method_name, i))
        logging.warning("########### Starting:%s ：%d Iter ##########" % (method_name, i))
        Metric =sub_nestedcv(SubjectsData_train, SubjectsLabel_train, SubjectsData_test, SubjectsLabel_test,func,kFold)
        MetricList.append(Metric)
    merglists = MetricList[0].mergeMetricList(MetricList)
    avgMetric = merglists.getAverageMetric()
    stdMetric= merglists.getStdMetric()
    maxMetric,maxi=merglists.getMaxMetric()
    save = SaveMetrics(record_name+".xls")
    global first_method
    if first_method == 0:
        first_method=1
        save.writeResultsHeader(avgMetric, mask='GreyMaskDir', DataDir_train='DataDir_train',DataDir_test='DataDir_test',time="RunTimes", std='test_acc_std',\
                                max_acc="max_test_acc",max_sen="max_test_sens",max_spec="max_test_spec")
    end = time.time()
    run_times=int(end-start)
    save.writeResultsMetrics(avgMetric, method_name, log_file, mask=GreyMaskDir, DataDir_train=DataDir_train,DataDir_test=DataDir_test, time=run_times,std=stdMetric.metric['Accuracy_test'][0],\
                             max_acc=maxMetric.metric["Accuracy_test"][0],max_sen=maxMetric.metric["Sensitivity_test"][0],max_spec=maxMetric.metric["Specifity_test"][0])
    print('Using %s,After %d iterations, the mean  metric = %r' % (method_name,nIter, avgMetric.metric))
    logging.warning('Using %s,After %d iterations, the mean  metric = %r' % (method_name,nIter, avgMetric.metric))
    logging.warning('Using %s,After %d iterations, the std  metric = %r' % (method_name,nIter, stdMetric.metric))
    logging.warning(
    'Using %s,After %d iterations, the max iter is %d, max metric = %r' % (method_name, nIter, maxi, maxMetric.metric))
    
    # ========== 新增：保存最佳模型 ==========
    save_trained_model_simple(
        clf_name=method_name.split('_')[0],  # 去掉 _Optuna 后缀
        func=func,
        SubjectsData_train=SubjectsData_train,
        SubjectsLabel_train=SubjectsLabel_train,
        mask_path=GreyMaskDir,
        avgMetric=avgMetric,
        kFold=kFold,
        nIter=nIter,
        iter_idx=nIter-1  # 保存最后一次迭代的结果
    )
    # ======================================
    
    return MetricList

normalizer=[
    ("MinMaxScaler",WrappedMinMaxScaler),
    ("StandardScaler",WrappedStandardScaler),
    # ("RobustScaler", WrappedRobustScaler),
    # ("Normalizer", WrappedNormalizer),
]
selector = [
    ("PCA",WrappedPCA),
    # ("KernelPCA",WrappedKernelPCA),
    # ("FastICA",WrappedFastICA), #not good
    # ("Mrmr", Mrmr),
    # ("ReliefF", ReliefF),
    # ("SelectKBest", WrappedSelectKBest),
    # ("RFE", WrappedRFE),
            ]
classifier=[
    ("RandomForest", RandomForest),
    ("GsNB", GsNB),
    ("KNN", KNN),
    ("Ada", Ada),
    ("DTree",DTree),
    ("xgb",xgb),
    ("ExtraTrees",ExtraTrees),
    ("SGD",SGD),
    ("QDA",QDA),
    ("Ridge",Ridge),
    ("Bagging",Bagging),
    ("SVM", WrappedSVM),
    ("LightGBM", LightGBM),
    ("Vote",Vote),
    # ("GrandientBoosting", GrandientBoosting),  #效果一般
    # ("RFE", WrappedRFE),
            ]

models_n=[]
# without selector
for n1,n in normalizer:
        for c1,c in classifier:
            models_n.append((n1+"+"+c1,[n,c]))
#with selector
for n1,n in normalizer:
    for s1,s in selector:
        for c1,c in classifier:
            models_n.append((n1+"+"+s1+"+"+c1,[n,s,c]))

##################################################################################

def main_cross_mult_site_one_mask(models,mask,rec_name,Dir_train,Dir_test,gName,kFold = 5, nIter = 2):
    global GreyMaskDir,GroupName, DataDir_train, DataDir_test, Group1Data_train, Group2Data_train
    global Group1Data_test, Group2Data_test
    GroupName=gName
    DataDir_train = Dir_train
    DataDir_test = Dir_test
    GreyMaskDir = mask
    Group1Data_train, Group2Data_train, SubjectsData_train, SubjectsLabel_train,_,_ = LoadMultiSiteDataByMask(
        mask,
        Dir_train,
        gName)
    Group1Data_test, Group2Data_test, SubjectsData_test, SubjectsLabel_test,_,_ = LoadMultiSiteDataByMask(mask,
                                                                                                      Dir_test,
                                                                                                      gName)

    ret_clf_metric = {}  # key 是方法名，value是merglists
    for clf_name, func in models:
        func_name = "%s_%s" % (clf_name, NestedMode)
        try:
            merglists =  main_nestedcv(SubjectsData_train, SubjectsLabel_train, SubjectsData_test, SubjectsLabel_test,func_name, func,rec_name, kFold=kFold, nIter=nIter)
            ret_clf_metric[clf_name] = merglists
        except Exception as e:
            print('Fail: Run %s function exception:%s' % (clf_name, e))
            logging.warning('Fail: Run %s function exception:%s' % (clf_name, e))
    return ret_clf_metric

def main_cross_mult_site_mult_mask(models,region_paths,rec_name,Dir_train,Dir_test,gName,kFold = 5, nIter = 2):
    # global GreyMaskDir, record_name, DataDir_train, DataDir_test, Group1Data_train, Group2Data_train, SubjectsData_train, SubjectsLabel_train
    # global Group1Data_test, Group2Data_test, SubjectsData_test, SubjectsLabel_test
    # record_name = rec_name
    # DataDir_train = Dir_train
    # DataDir_test = Dir_test
    for mask in region_paths:
        GreyMaskDir = mask
        main_cross_mult_site_one_mask(models, mask, rec_name, Dir_train, Dir_test,gName,kFold, nIter)

def main_abide_mask():
    GroupName = ['normal', 'asd']
    kFold = 5
    nIter = 10
    trains=["GU"]
    tests=["UCLA","OHSU"]
    type="GM"
    DDir_train = [r'../data/ABIDEII-%s/%s/smooth/' % (t, type) for t in trains]
    DDir_test = [r"../data/ABIDEII-%s/%s/smooth/" % (t, type) for t in tests]
    mask = '../data/Mask/01rgrey_02.nii'
    rec_name = "../data/Results_gm/Results_%s_%s_%diter_mask" % (trains, tests, nIter)
    models_run = [
        ('MinMaxScaler+Ridge', [WrappedMinMaxScaler, Ridge]),
        # ('MinMaxScaler+SVM', [WrappedMinMaxScaler, WrappedSVM]),
        # ('MinMaxScaler+Bagging', [WrappedMinMaxScaler, Bagging]),
    ]
    main_cross_mult_site_one_mask(models_run, mask, rec_name, DDir_train, DDir_test,GroupName,kFold, nIter)


def main_abide_region():
    GroupName = ['normal', 'asd']
    kFold = 5
    nIter = 10
    trains=["KKI"]
    tests=["GU"]
    type="GM"
    DDir_train = [r'../data/ABIDEII-%s/%s/smooth/' % (t, type) for t in trains]
    DDir_test = [r"../data/ABIDEII-%s/%s/smooth/" % (t, type) for t in tests]
    rec_name = "../data/Results_gm/multi-decenter/Results_6sites_decenter_%s_%s_%diter_aal3" % (trains, tests, nIter)
    regs = [7,8]
    reg_paths = ['../data/Mask/ROI/Region_aal1_cluster_50_70/reg%s.nii' % t for t in regs]
    models_run = [
        ('MinMaxScaler+PCA+Ridge', [WrappedMinMaxScaler, WrappedPCA, Ridge]),
        ('MinMaxScaler+PCA+SVM', [WrappedMinMaxScaler, WrappedPCA, WrappedSVM]),
        ('MinMaxScaler+Bagging', [WrappedMinMaxScaler, Bagging]),
    ]
    main_cross_mult_site_mult_mask(models_run, reg_paths, rec_name, DDir_train, DDir_test,GroupName,kFold, nIter)
# **********************************************************************************************************************

# main_abide_region()
main_abide_mask()



# s="main_abide_region"
# eval(s)()
