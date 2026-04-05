from sklearn.feature_selection import RFE,SelectKBest,chi2,f_classif,mutual_info_classif,f_regression,mutual_info_regression,SelectPercentile,SelectFdr,SelectFpr,SelectFwe,GenericUnivariateSelect
import optuna
class TunedParaRang:
    def __init__(self,totalFeatures,sampleNum):
        self.totalFeatures=totalFeatures
        self.sampleNum=sampleNum
        self.neibers=0.25
        self.max_depth=0.3
        self.minFeatures=1
        ##for SVM
        self.svm_C=optuna.distributions.LogUniformDistribution(1e-10, 1e10)
        ### for PCA
        self.pca_n_components=optuna.distributions.UniformDistribution(0.6, 0.99)
        ####for lightGBM
        self.gbm_max_depth=optuna.distributions.IntUniformDistribution(3, int(self.sampleNum*self.max_depth))
        self.gbm_learning_rate=optuna.distributions.UniformDistribution(0.01, 0.15)
        self.gbm_lambda_l1=optuna.distributions.UniformDistribution(1e-8, 10.0)
        self.gbm_lambda_l2=optuna.distributions.UniformDistribution(1e-8, 10.0)
        self.gbm_num_leaves=optuna.distributions.IntUniformDistribution(2, 100)
        self.gbm_feature_fraction=optuna.distributions.UniformDistribution(0.4, 1.0)
        self.gbm_bagging_fraction=optuna.distributions.UniformDistribution(0.4, 1.0)
        self.gbm_cat_smooth= optuna.distributions.IntUniformDistribution(1, 35)


        ###### for random forest
        self.rf_n_estimators=optuna.distributions.IntUniformDistribution(3, 30)
        self.rf_max_depth=optuna.distributions.IntUniformDistribution(3, int(self.sampleNum*self.max_depth))

        #########for stablity
        self.stable_threshold=optuna.distributions.UniformDistribution(0.5, 1)

        ######mrmr
        self.mrmr_n_features_select=optuna.distributions.IntUniformDistribution(self.minFeatures,self.totalFeatures)

        ######relief
        self.relief_n_features_select= optuna.distributions.IntUniformDistribution(self.minFeatures,self.totalFeatures)

        #####for SelectKBest
        self.skbest_k=optuna.distributions.IntUniformDistribution(self.minFeatures,self.totalFeatures)
        self.skbest_scoreFunc=optuna.distributions.CategoricalDistribution(
            (chi2, f_classif, mutual_info_classif,f_regression,mutual_info_regression))

        ####for Grandient Boosting
        ####tree parameters
        self.gb_min_samples_split = optuna.distributions.IntUniformDistribution(1,100) # the 0.5%~1% of the number of samples
        self.gb_min_samples_leaf = optuna.distributions.IntUniformDistribution(1,100)
        self.gb_min_weight_fraction_leaf = optuna.distributions.UniformDistribution(0.1,0.9)
        self.gb_max_depth = optuna.distributions.IntUniformDistribution(1,int(self.sampleNum*self.max_depth))
        self.gb_max_leaf_nodes = optuna.distributions.IntUniformDistribution(1,100)

        ####boostig parameters
        self.gb_learning_rate = optuna.distributions.UniformDistribution(0.01, 0.15)
        self.gb_n_estimators = optuna.distributions.IntUniformDistribution(3,30)
        self.gb_subsample = optuna.distributions.UniformDistribution(0.1,0.9) # 0.8 for most cases
        self.gb_max_features = optuna.distributions.IntUniformDistribution(self.minFeatures,self.totalFeatures)

        ####for boruta
        self.boruta_perc = optuna.distributions.IntUniformDistribution(80,100)

        ####for rfe
        self.rfe_features = optuna.distributions.IntUniformDistribution(self.minFeatures,self.totalFeatures)

        #ExtraTrees
        self.et_min_samples_split = optuna.distributions.IntUniformDistribution(1,100) # the 0.5%~1% of the number of samples
        self.et_min_samples_leaf = optuna.distributions.IntUniformDistribution(1,100)
        self.et_n_estimators = optuna.distributions.IntUniformDistribution(3,30)
        self.et_max_features = optuna.distributions.IntUniformDistribution(self.minFeatures, self.totalFeatures)

        #knn
        self.knn_n_neighbors=optuna.distributions.IntUniformDistribution(3,int(self.sampleNum*self.neibers))
        self.knn_weights=optuna.distributions.CategoricalDistribution(
            ("uniform","distance"))

        #ada
        self.ada_n_estimators=optuna.distributions.IntUniformDistribution(3,30)

        #dtree
        self.dtree_min_samples_split = optuna.distributions.IntUniformDistribution(1,100) # the 0.5%~1% of the number of samples
        self.dtree_min_samples_leaf = optuna.distributions.IntUniformDistribution(1,100)
        self.dtree_min_weight_fraction_leaf = optuna.distributions.UniformDistribution(0.1,0.9)
        self.dtree_max_depth = optuna.distributions.IntUniformDistribution(1,int(self.sampleNum*self.max_depth))
        self.dtree_max_leaf_nodes = optuna.distributions.IntUniformDistribution(1,100)

        #log
        self.log_C=optuna.distributions.LogUniformDistribution(1e-10, 1e10)

        ####for xgboost
        ####tree parameters
        self.xgb_min_samples_split = optuna.distributions.IntUniformDistribution(1,100) # the 0.5%~1% of the number of samples
        self.xgb_min_samples_leaf = optuna.distributions.IntUniformDistribution(1,100)
        self.xgb_min_weight_fraction_leaf = optuna.distributions.UniformDistribution(0.1,0.9)
        self.xgb_max_depth = optuna.distributions.IntUniformDistribution(1,int(self.sampleNum*self.max_depth))
        self.xgb_max_leaf_nodes = optuna.distributions.IntUniformDistribution(1,100)

        ####boostig parameters
        self.xgb_learning_rate = optuna.distributions.UniformDistribution(0.01, 0.15)
        self.xgb_n_estimators = optuna.distributions.IntUniformDistribution(3,30)
        self.xgb_subsample = optuna.distributions.UniformDistribution(0.1,0.9) # 0.8 for most cases
        self.xgb_max_features = optuna.distributions.IntUniformDistribution(self.minFeatures,self.totalFeatures)

        #for sgd
        self.sgd_loss=optuna.distributions.CategoricalDistribution(
            ("hinge","modified_huber","log"))
        self.sgd_penalty = optuna.distributions.CategoricalDistribution(
            ("l2", "l1", "elasticnet"))

        #ridge
        self.ridge_alpha=optuna.distributions.LogUniformDistribution(1e-10, 1e10)

        #bagging
        self.bag_n_estimators = optuna.distributions.IntUniformDistribution(3, 30)
        self.bag_max_samples = optuna.distributions.UniformDistribution(0.5,1.0)
        self.bag_max_features = optuna.distributions.UniformDistribution(0.5, 1.0)

        #kernalpca
        self.kpca_n_components = optuna.distributions.UniformDistribution(0.6, 0.99)
        self.kpca_kernel = optuna.distributions.CategoricalDistribution(
            ("linear","poly","rbf","sigmoid","cosine","precomputed"))

        #for se
        self.se_n_components = optuna.distributions.UniformDistribution(0.6, 0.99)
        self.se_affinity = optuna.distributions.CategoricalDistribution(
            ("nearest_neighbors", "rbf", "precomputed", "precomputed_nearest_neighbors"))
        self.se_n_neighbors = optuna.distributions.IntUniformDistribution(3,int(self.sampleNum*self.neibers))
        self.se_eigen_solver = optuna.distributions.CategoricalDistribution(
            ("arpack", "lobpcg", "amg"))

        #for feature hash
        self.fhash_n_features = optuna.distributions.IntUniformDistribution(self.minFeatures, self.totalFeatures)

        # for fast ica
        self.fica_n_components = optuna.distributions.IntUniformDistribution(self.minFeatures, int(self.totalFeatures*0.85))

        # for  vote
        self.vot_xgb_n_estimators = optuna.distributions.IntUniformDistribution(10,200)
        self.vot_gradientboosting_n_estimators = optuna.distributions.IntUniformDistribution(10, 200)

        #for GaussianProcessClassifier
        self.gpc_length_scale=optuna.distributions.UniformDistribution(0.6, 2.0)

        #for Elastic Net
        self.en_alpha=optuna.distributions.UniformDistribution(0.6, 2.0)

        #for KernelRidge
        self.kr_alpha=optuna.distributions.UniformDistribution(0.6, 2.0)

