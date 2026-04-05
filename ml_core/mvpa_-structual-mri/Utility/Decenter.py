import numpy as np
import os
class DecenterArgs:
    def __init__(self,cov_path,cols,site,save_nii=False,do_decenter=0):
        self.cov_path=cov_path
        self.cols = cols
        self.do_decenter = do_decenter#0表示不去中心，1表示combat去中心2表示线性回归
        self.save_nii=save_nii
        self.site=site

########  For ABIDE get cover  by file list #####
def GetCoverByFilelistAbide(filelist,covars_all,GroupName):
    list_id=[]
    label= np.zeros([len(filelist)])
    i=0
    for file in filelist:
        (filepath, tempfilename) = os.path.split(file)
        id=tempfilename[7:12]#TODO:改为传参获得编号在字符串中的位置。
        list_id.append(int(id))
        (fp, grpname) = os.path.split(filepath)
        if grpname==GroupName[0]:
            label[i]=1
        elif grpname==GroupName[1]:
            label[i] = 0
        else:
            print("Fail:group name not correct.")
        i=i+1
    covars= covars_all[covars_all['SUB_ID'].isin(list_id)]  #TODO:改为传参获得id的列名
    covars['SUB_ID'] = covars['SUB_ID'].astype('category')
    covars['SUB_ID']=covars['SUB_ID'].cat.set_categories(list_id)
    covars=covars.sort_values(by='SUB_ID')
    covars = covars.reset_index(drop=True)
    return covars,label
