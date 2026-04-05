import sys
sys.path.append('/Utility')
sys.path.append('/ClassifyFunc')

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

NestedMode = "Optuna" # Manul/Optuna/Hyopt/None
if NestedMode == "Optuna":
    from ClassifyFunc.NestedCV_Optuna import NestedCV_kFold
    from ClassifyFunc.ModelSettings_Optuna import TunedParaRang
if NestedMode == "Hyopt":
    from ClassifyFunc.NestedCV_Hyopt import NestedCV_kFold
    from ClassifyFunc.ModelSettings_Hyopt import TunedParaRang
if NestedMode == "Manul":
    from ClassifyFunc.NestedCV_Manul import NestedCV_kFold
    from ClassifyFunc.ModelSettings_NestManul import TunedParaRang

# **********************************************************************************************************************
last_log_handler=[]
first_method=0#用来标记是否记录本次运行的reslut表头。
def init_logfile(method_name,kFold,nIter,record_name):
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
    logging.warning("----DataDir:%s" % (DataDir))
    logging.warning("----GroupName:%r" % (GroupName))
    logging.warning("----group1:%d" % (Group1Data.shape[0]))
    logging.warning("----group2:%d" % (Group2Data.shape[0]))
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

#参数含义：数据X，标签Y,方法名称，函数名，当前迭代次数，总折数，总迭代数
def sub_nestedcv(SubjectsData, SubjectsLabel,method_name, func,citer, record_name,kFold = 5):
    ResultantFolder = record_name+'/'+method_name+'/HC_PD/'
    NormalizeFlag = 'True'  # True/False
    NormalzeMode = 'MinMaxScaler'  # StandardScaler/MinMaxScaler/Normalizer/None
    sampleNum, totalFeatures = np.shape(SubjectsData)
    rang=TunedParaRang(totalFeatures,sampleNum)
    tuned_parameters, model = ConstructModel(rang,func)
    printTunedParam(tuned_parameters)
    Metric=NestedCV_kFold(SubjectsData, SubjectsLabel,ResultantFolder,kFold, NormalizeFlag, NormalzeMode,\
                                     model,tuned_parameters,citer)
    return Metric

def main_nestedcv_iters(SubjectsData, SubjectsLabel,clf_name,func,kFold,nIter,rec_name):
    MetricList = []
    try:
        start = time.time()
        log_file = init_logfile(clf_name, kFold, nIter,rec_name)
        logging.warning("########### Starting:%s  %d Fold %d Iter ##########" % (clf_name, kFold, nIter))
        for i in range(nIter):
            print("########### Starting:%s ：%d Iter ##########" % (clf_name, i))
            logging.warning("########### Starting:%s ：%d Iter ##########" % (clf_name, i))
            Metric= sub_nestedcv(SubjectsData, SubjectsLabel, clf_name, func, i,rec_name, kFold=kFold)
            MetricList.append(Metric)
        end = time.time()
        run_times = int(end - start)
    except Exception as e:
        print('Fail: Run %s function exception:%s' % (clf_name, e))
        logging.warning('Fail: Run %s function exception:%s' % (clf_name, e))
    merglists = MetricList[0].mergeMetricList(MetricList)
    avgMetric = merglists.getAverageMetric()
    stdMetric = merglists.getStdMetric()
    save = SaveMetrics(rec_name + ".xls")
    global first_method
    if first_method == 0:
        first_method = 1
        save.writeResultsHeader(avgMetric, mask='GreyMaskDir', DataDir='DataDir', time="RunTimes",
                                std_acc='test_acc_std',std_sens='test_sens_std',std_spec='test_spec_std')
    save.writeResultsMetrics(avgMetric, clf_name, log_file, mask=GreyMaskDir, DataDir=DataDir,
                             time=run_times, std_acc=stdMetric.metric['Accuracy_test'][0],
                             std_sens=stdMetric.metric['Sensitivity_test'][0],std_spec=stdMetric.metric['Specifity_test'][0])
    print('Using %s,After %d iterations, the mean  metric = %r' % (clf_name, nIter, avgMetric.metric))
    logging.warning(
        'Using %s,After %d iterations, the mean  metric = %r' % (clf_name, nIter, avgMetric.metric))
    logging.warning(
        'Using %s,After %d iterations, the std  metric = %r' % (clf_name, nIter, stdMetric.metric))
    return MetricList

normalizer=[
    ("MinMaxScaler",WrappedMinMaxScaler),
    # ("StandardScaler",WrappedStandardScaler),
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
    ("ExtraTrees",ExtraTrees),
    ("SGD",SGD),
    ("Ridge",Ridge),
    ("Bagging",Bagging),
    ("SVM", WrappedSVM),
    ("LightGBM", LightGBM),

    ("QDA",QDA),  # run  to long for pd et more than 20h  for 1 iter
    ("xgb",xgb), # run  to long for pd et more than 1h  for 1 iter  run  later
    # ("GrandientBoosting", GrandientBoosting),  #效果一般
    # ("Vote",Vote),
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

###################################################
def inner_one_mask(models, mask_path, rec_name, dir,kFold, nIter, gName):
    global GreyMaskDir, DataDir, Group1Data,Group2Data,GroupName
    DataDir=dir
    GreyMaskDir = mask_path
    GroupName=gName
    Group1Data,Group2Data,SubjectsData,SubjectsLabel,_,_=LoadMultiSiteDataByMask(mask_path, dir, GroupName,0)
    ret_clf_metric={}#key 是方法名，value是merglists
    for clf_name,func in models:
        func_name="%s_%s"%(clf_name,NestedMode)
        print("Starting Nested: %s"%func_name)
        merglists=main_nestedcv_iters(SubjectsData, SubjectsLabel, clf_name, func, kFold, nIter, rec_name)
        ret_clf_metric[clf_name]=merglists
    return ret_clf_metric

def inner_mult_masks(models, mask_paths, rec_name, dir,kFold, nIter, GroupName):
    ret_metric_list=[]#数组每个都是一个hash，分别对应不同方法的运行结果，数组对应结果和mask结果一致
    for mask in mask_paths:
        ret_metric_list.append(inner_one_mask(models, mask, rec_name, dir,kFold, nIter, GroupName))
    return ret_metric_list
def main_abide_gu_region():
    kFold = 5
    nIter = 10
    GroupName =['normal','asd']
    site=["UCLA"]
    type="GM"
    rec_name = "../data/Results_gm/%s_gu/Results_%s_%diter" % (type, site, nIter)
    DDir = [r"../data/ABIDEII-%s/%s/smooth/" % (t, type) for t in site]
    regs=[2,14]#gm
    reg_paths=['../data/Mask/ROI/Region_aal1_cluster_50_70/reg%s.nii' %  t for t in regs]
    models_selected = [
        # good clf for gm
        ('MinMaxScaler+Bagging', [WrappedMinMaxScaler, Bagging]),
        # ('MinMaxScaler+PCA+Ridge', [WrappedMinMaxScaler, WrappedPCA, Ridge]),
        # ('MinMaxScaler+xgb', [WrappedMinMaxScaler, xgb]),
        # ('MinMaxScaler+PCA+SVM', [WrappedMinMaxScaler, WrappedPCA, WrappedSVM]),
        ]
    inner_mult_masks(models_selected, reg_paths, rec_name, DDir,kFold, nIter, GroupName)

def main_abide_gu_mask():
    kFold = 5
    nIter = 10
    GroupName =['normal','asd']
    site=["GU"]
    type="GM"
    rec_name = "../data/Results_gm/Results_%s_%diter_mask_e70" % (site, nIter)
    DDir = [r"../data/ABIDEII-%s/%s/smooth/" % (t, type) for t in site]
    # mask="../data/Mask/mask_e70_searchlight_pca_svc_roc_auc_result_GU_gm.nii"
    mask = "../data/Mask/ROI/Region_aal1_cluster_50_70/reg1.nii"

    models_selected = [
        # good clf for gm
        # ('MinMaxScaler+RandomForest', [WrappedMinMaxScaler, RandomForest]),
        ('MinMaxScaler+pca+SVM', [WrappedMinMaxScaler, WrappedPCA, WrappedSVM]),
        # ('MinMaxScaler+Bagging', [WrappedMinMaxScaler, Bagging]),
    ]
    inner_one_mask(models_selected, mask, rec_name, DDir,kFold, nIter, GroupName)

# main_abide_gu_mask()
main_abide_gu_region()