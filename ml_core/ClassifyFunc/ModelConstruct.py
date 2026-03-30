import sys
sys.path.append('/home/deep/research/MVPA/PD_cliu_202006/python/stability-selection-master/stability_selection')

from sklearn.svm import  LinearSVC,SVC
from sklearn.decomposition import PCA
from sklearn.pipeline import Pipeline
from Utility.SelectFeature import SelectFeatures,TwoSampleTestSelection,TwoSampleTest
from sklearn.feature_selection import RFE,SelectKBest,chi2,f_classif,mutual_info_classif,f_regression,mutual_info_regression,SelectPercentile,SelectFdr,SelectFpr,SelectFwe,GenericUnivariateSelect
# from stability_selection import StabilitySelection
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingClassifier
from skfeature.function.information_theoretical_based import MRMR
import lightgbm as lgb
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.preprocessing import MinMaxScaler,StandardScaler,RobustScaler,Normalizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import ExtraTreesClassifier
from skrebate import relieff
from boruta import BorutaPy
from sklearn.calibration import CalibratedClassifierCV
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import AdaBoostClassifier
from sklearn.tree import  DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier
from sklearn.linear_model import SGDClassifier,RidgeClassifier
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis
from sklearn.ensemble import BaggingClassifier
from sklearn.decomposition import KernelPCA
from sklearn.manifold import  SpectralEmbedding
from sklearn.decomposition import FastICA
from sklearn.feature_extraction import FeatureHasher
from mlxtend.classifier import EnsembleVoteClassifier
from sklearn.ensemble import VotingClassifier
from sklearn.gaussian_process import GaussianProcessClassifier
from sklearn.gaussian_process.kernels import RBF
from sklearn.linear_model import ElasticNet
from sklearn.kernel_ridge import KernelRidge

#################################
######data preprocessing
###1.MinMaxScaler
###2.StandardScaler
###3.Normalizer
###4.RobustScaler
def WrappedMinMaxScaler():
    model=MinMaxScaler()
    return model
def WrappedStandardScaler():
    model=StandardScaler()
    return model
def WrappedNormalizer():
    model=Normalizer()
    return model
def WrappedRobustScaler():
    model=RobustScaler()
    return model

######feature engineering################
####1.WrappedPCA
####2.WrappedLDA
####3.Mrmr
####4.ReliefF
####5.StabilityLR
####6.WrappedSelectKBest
####7.BorutaRandomForest
def ttest(tuned_para_range):
    tuned_params = {
    }
    model = TwoSampleTestSelection(estimator=TwoSampleTest,pVal=0.5)
    return tuned_params,model


def WrappedPCA(tuned_para_range):
    tuned_params = {
        "selector__n_components": tuned_para_range.pca_n_components
    }
    model = PCA()
    return tuned_params,model

def WrappedLDA(tuned_para_range):
    tuned_parameters = {
    }
    model = LinearDiscriminantAnalysis(n_components=1)
    return tuned_parameters, model

def Mrmr(tuned_para_range):
    tuned_parameters = {
        'selector__n_features_select':tuned_para_range.mrmr_n_features_select
    }
    model = SelectFeatures(MRMR.mrmr,mode='index')

    return tuned_parameters,model

def ReliefF(tuned_para_range):
    tuned_parameters = {
        'selector__n_features_to_select':tuned_para_range.relief_n_features_select,
    }
    model=relieff.ReliefF()

    # model = SelectFeatures(relieff.ReliefF, mode='index')
    return tuned_parameters, model

# def StabilityLR(tuned_para_range):
#     tuned_parameters = {
#         'selector__threshold':tuned_para_range.stable_threshold,
#     }
#     base_estimator = LogisticRegression(C=1, penalty='l2', solver='liblinear')
#     model = StabilitySelection(base_estimator=base_estimator)
#     return tuned_parameters, model

def WrappedSelectKBest(tuned_para_range):
    tuned_parameters = {
        'selector__score_func':tuned_para_range.skbest_scoreFunc,
        'selector__k':tuned_para_range.skbest_k
    }
    model = SelectKBest()
    return tuned_parameters, model

def BorutaRandomForest(tuned_para_range):
    tuned_parameters = {
        'selector__perc':tuned_para_range.boruta_perc,
    }
    estimator = RandomForestClassifier(n_jobs=-1,class_weight='balanced',max_depth=5)
    model = BorutaPy(estimator=estimator, n_estimators='auto',verbose = 2,random_state=1,max_iter=10)
    return tuned_parameters, model

def WrappedKernelPCA(tuned_para_range):
    tuned_parameters = {
        'selector__n_components':tuned_para_range.kpca_n_components,
        'selector__kernel':tuned_para_range.kpca_kernel
    }
    model = KernelPCA()
    return tuned_parameters, model

def WrappedFastICA(tuned_para_range):
    tuned_parameters = {
        'selector__n_components':tuned_para_range.fica_n_components,
    }
    model = FastICA()
    return tuned_parameters, model
#to debug
def WrappedFeatureHasher(tuned_para_range):
    tuned_parameters = {
        'selector__n_features':tuned_para_range.fhash_n_features,
    }
    model = FeatureHasher()
    return tuned_parameters, model

def WrappedSpectralEmbedding(tuned_para_range):
    tuned_parameters = {
        'selector__n_components':tuned_para_range.se_n_components,
        'selector__affinity': tuned_para_range.se_affinity,
        'selector__eigen_solver':tuned_para_range.se_eigen_solver,
        'selector__n_neighbors': tuned_para_range.se_n_neighbors,
    }
    model = SpectralEmbedding()
    return tuned_parameters, model
def WrappedElasticNet(tuned_para_range):
    tuned_parameters = {
        'selector__alpha':tuned_para_range.en_alpha,
    }
    model = ElasticNet()
    return tuned_parameters, model
######classifiers################
###1.SVM
###2.LightGBM
###3.RandomForest
###4.GrandientBoosting
###5.WrappedRFE
def WrappedSVM(tuned_para_range):
    tuned_params = {
        'classifier__base_estimator__C':tuned_para_range.svm_C
    }
    model = LinearSVC(class_weight='balanced')
    model = CalibratedClassifierCV(base_estimator=model)
    ######for predict probability
    # predictLabel = model.predict(y_test)
    # model.predict_proba(predictLabel)

    # model = SVC(kernel='linear', probability=True)

    return tuned_params,model
def WrappedSVM_COEF(tuned_para_range):
    tuned_params = {
        'classifier__C': tuned_para_range.svm_C
    }
    model = SVC(kernel='linear', probability=True)

    return tuned_params,model
def LightGBM(tuned_para_range):
    tuned_parameters = {
        "classifier__max_depth": tuned_para_range.gbm_max_depth,
        "classifier__learning_rate": tuned_para_range.gbm_learning_rate,
        "classifier__lambda_l1": tuned_para_range.gbm_lambda_l1,
        "classifier__lambda_l2": tuned_para_range.gbm_lambda_l2,
        "classifier__num_leaves": tuned_para_range.gbm_num_leaves,
        "classifier__feature_fraction": tuned_para_range.gbm_feature_fraction,
        "classifier__bagging_fraction": tuned_para_range.gbm_bagging_fraction,
        "classifier__cat_smooth": tuned_para_range.gbm_cat_smooth
    }
    ##################################
    model = lgb.LGBMClassifier()
    return tuned_parameters, model

def RandomForest(tuned_para_range):
    tuned_parameters = {
        "classifier__n_estimators":tuned_para_range.rf_n_estimators,
        "classifier__max_depth": tuned_para_range.rf_max_depth
    }
    model =  RandomForestClassifier(class_weight='balanced',max_features='sqrt')

    return tuned_parameters,model


def GrandientBoosting(tuned_para_range):
    tuned_parameters = {
        "classifier__min_samples_leaf":tuned_para_range.gb_min_samples_leaf,
        "classifier__min_samples_split": tuned_para_range.gb_min_samples_split,
        "classifier__min_weight_fraction_leaf": tuned_para_range.gb_min_weight_fraction_leaf,
        "classifier__max_depth": tuned_para_range.gb_max_depth,
        "classifier__max_leaf_nodes": tuned_para_range.gb_max_leaf_nodes,
        "classifier__learning_rate": tuned_para_range.gb_learning_rate,
        "classifier__n_estimators": tuned_para_range.gb_n_estimators,
        "classifier__subsample": tuned_para_range.gb_subsample,
        "classifier__max_features":tuned_para_range.gb_max_features,
    }
    model = GradientBoostingClassifier()
    return tuned_parameters, model

def WrappedRFE(tuned_para_range):
    tuned_parameters = {
        'classifier__n_features_to_select':tuned_para_range.rfe_features,
    }
    estimator = LinearSVC(class_weight='balanced')
    model = RFE(estimator=estimator)
    return tuned_parameters, model

def ExtraTrees(tuned_para_range):
    tuned_parameters = {
        "classifier__min_samples_leaf":tuned_para_range.et_min_samples_leaf,
        "classifier__min_samples_split": tuned_para_range.et_min_samples_split,
        "classifier__n_estimators": tuned_para_range.et_n_estimators,
        "classifier__max_features":tuned_para_range.et_max_features,
    }
    model = ExtraTreesClassifier(bootstrap=True, criterion="entropy")#, max_features=0.6500000000000001)
                                 # , \
                                 # min_samples_leaf=3, min_samples_split=11, n_estimators=100)
    return tuned_parameters, model

def GsNB(tuned_para_range):
    tuned_parameters = {
    }
    model = GaussianNB()
    return tuned_parameters, model
# from sklearn.pipeline import make_pipeline, make_union
# from sklearn.tree import DecisionTreeClassifier
# from tpot.builtins import StackingEstimator
# from sklearn.neighbors import KNeighborsClassifier
# def Test(tuned_para_range):
#     tuned_parameters = {
#     }
#     model = make_pipeline(
#         StackingEstimator(
#             estimator=DecisionTreeClassifier(criterion="gini", max_depth=8, min_samples_leaf=6, min_samples_split=12)),
#         KNeighborsClassifier(n_neighbors=28, p=2, weights="distance")
#     )
#     return tuned_parameters, model

def KNN(tuned_para_range):
        tuned_parameters = {
        "classifier__n_neighbors":tuned_para_range.knn_n_neighbors,
        "classifier__weights": tuned_para_range.knn_weights,
        }
        model = KNeighborsClassifier()
        return tuned_parameters, model


def Ada(tuned_para_range):
    tuned_parameters = {
        "classifier__n_estimators": tuned_para_range.ada_n_estimators,
    }
    model = AdaBoostClassifier()
    return tuned_parameters, model

def DTree(tuned_para_range):
    tuned_parameters = {
        "classifier__min_samples_leaf": tuned_para_range.dtree_min_samples_leaf,
        "classifier__min_samples_split": tuned_para_range.dtree_min_samples_split,
        "classifier__min_weight_fraction_leaf": tuned_para_range.dtree_min_weight_fraction_leaf,
        "classifier__max_depth": tuned_para_range.dtree_max_depth,
        "classifier__max_leaf_nodes": tuned_para_range.dtree_max_leaf_nodes,

    }
    model = DecisionTreeClassifier()
    return tuned_parameters, model

def Log(tuned_para_range):
    tuned_parameters = {
        "classifier__C": tuned_para_range.log_C,
    }
    model = LogisticRegression()
    return tuned_parameters, model

def xgb(tuned_para_range):
    tuned_parameters = {
        "classifier__min_samples_leaf":tuned_para_range.xgb_min_samples_leaf,
        "classifier__min_samples_split": tuned_para_range.xgb_min_samples_split,
        "classifier__min_weight_fraction_leaf": tuned_para_range.xgb_min_weight_fraction_leaf,
        "classifier__max_depth": tuned_para_range.xgb_max_depth,
        "classifier__max_leaf_nodes": tuned_para_range.xgb_max_leaf_nodes,
        "classifier__learning_rate": tuned_para_range.xgb_learning_rate,
        "classifier__n_estimators": tuned_para_range.xgb_n_estimators,
        "classifier__subsample": tuned_para_range.xgb_subsample,
        "classifier__max_features":tuned_para_range.xgb_max_features,
    }
    model = XGBClassifier()
    return tuned_parameters, model

def SGD(tuned_para_range):
    tuned_parameters = {
        "classifier__loss": tuned_para_range.sgd_loss,
        "classifier__penalty": tuned_para_range.sgd_penalty,
    }
    model = SGDClassifier()
    return tuned_parameters, model

def QDA(tuned_para_range):
    tuned_parameters = {
    }
    model = QuadraticDiscriminantAnalysis()
    return tuned_parameters, model
def Ridge(tuned_para_range):
    tuned_parameters = {
        "classifier__alpha": tuned_para_range.ridge_alpha,
    }
    model = RidgeClassifier(class_weight='balanced')
    return tuned_parameters, model

def Bagging(tuned_para_range):
    tuned_parameters = {
        "classifier__n_estimators": tuned_para_range.bag_n_estimators,
        "classifier__max_samples": tuned_para_range.bag_max_samples,
        "classifier__max_features": tuned_para_range.bag_max_features,
    }
    model = BaggingClassifier()
    return tuned_parameters, model

def Vote(tuned_para_range):
    tuned_parameters = {
        "classifier__xgbclassifier__n_estimators": tuned_para_range.vot_xgb_n_estimators,
        "classifier__gradientboostingclassifier__n_estimators": tuned_para_range.vot_gradientboosting_n_estimators,
    }
    svc= SVC()
    rf = RandomForestClassifier()
    # Bagging Classifiers
    bagging_clf = BaggingClassifier(rf, max_samples=0.4, max_features=10)
    ada_boost = AdaBoostClassifier()
    ada_boost_svc = AdaBoostClassifier(base_estimator=svc, algorithm='SAMME')
    grad_boost = GradientBoostingClassifier()
    xgb_boost = XGBClassifier()

    # Voting Classifiers
    # vclf = VotingClassifier(estimators=[('ada_boost', ada_boost), ('grad_boost', grad_boost),
    #                                     ('xgb_boost', xgb_boost), ('BaggingWithRF', bagging_clf)], voting='hard')
    # Grid Search
    # params = {'gradientboostingclassifier__n_estimators': [10, 200],
    #           'xgbclassifier__n_estimators': [10, 200]}

    model = EnsembleVoteClassifier(clfs=[ada_boost_svc, grad_boost, xgb_boost], voting='hard')
    # model=VotingClassifier(estimators=[ ada_boost, grad_boost, xgb_boost, bagging_clf], voting='hard')


    return tuned_parameters, model

#Gaussian Process Classification
def gpc(tuned_para_range):
    tuned_parameters = {
        # "classifier__RBF__length_scale": tuned_para_range.gpc_length_scale,
    }
    kernel = 1.0 * RBF()
    model = GaussianProcessClassifier(kernel=kernel)
    return tuned_parameters, model
#KernelRidge
def kridge(tuned_para_range):
    tuned_parameters = {
        # "classifier__alpha": tuned_para_range.kr_alpha,
    }
    model = KernelRidge()
    return tuned_parameters, model

def ConstructModel(rang,func):
    if len(func)==3:
        normalizer=func[0]()
        params_selector, selector=func[1](rang)
        params_classifier, classifier = func[2](rang)
        tuned_params = {**params_selector, **params_classifier}
        model = Pipeline(
            [
                ('normalizer', normalizer),
                ('selector', selector),
                ('classifier', classifier)
            ])
    else:
        if len(func)==2:
            normalizer = func[0]()
            params_classifier, classifier = func[1](rang)
            tuned_params = {**params_classifier}
            model = Pipeline(
                [
                    ('normalizer', normalizer),
                    ('classifier', classifier)
                ])
        else:
            if len(func)==4:
                normalizer=func[0]()
                params_selector, selector0=func[1](rang)
                params_classifier, selector = func[2](rang)
                params_classifier, classifier = func[3](rang)
                tuned_params = {**params_selector, **params_classifier}
                model = Pipeline(
                    [
                        ('normalizer', normalizer),
                        ('ttest',selector0),
                        ('selector', selector),
                        ('classifier', classifier)
                    ])
            else:
                params_classifier, classifier = func[0](rang)
                tuned_params = {**params_classifier}
                model = Pipeline(
                        [
                            ('classifier', classifier)
                        ])
    return tuned_params,model
