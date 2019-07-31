import os,shutil
import numpy as np

'''
Error handler function
It will try to change file permission and call the calling function again,
'''
def handleError(func, path, exc_info):
    print('Handling Error for file ' , path)
    print(exc_info)
    # Check if file access issue
    if not os.access(path, os.W_OK):
       print('Hello')
       # Try to change the permision of file
       os.chmod(path, stat.S_IWUSR)
       # call the calling function again
       func(path)

def index_marks(nrows, chunk_size):
    return range(1 * chunk_size, (nrows // chunk_size + 1) * chunk_size, chunk_size)

def split(dfm, chunk_size):
    indices = index_marks(dfm.shape[0], chunk_size)
    return np.split(dfm, indices)

def create_directory(path):
    try:
        os.makedirs(path)
    except OSError:
        print ("Creation of the directory %s failed" % path)
    else:
        print ("Successfully created the directory %s " % path)

def delete_directory(path):
    try:
        shutil.rmtree(path, onerror=handleError)
    except:
        print ("Deletion of the directory %s failed" % path)
    else:
        print ("Successfully deleted the directory %s " % path)

def calculate_metrics(TP, TN, FP, FN):

    ## Pre-calculations
    # PCP (Predicted condition positive) = TP+FP
    # PCN (Predicted condition negative) = FN+TN
    # CP (condition positive) = TP+FN
    # CN (condition negative) = TN+FP
    # TPOP (total population) =  CP + CN

    PCP = TP+FP
    PCN = FN+TN
    CP = TP+FN
    CN = TN+FP
    TPOP = CP+CN

    ## Metrics

    if (CP > 0):
        # True Positive Rate (TPR), also known as sensitivity or recall, is the proportion of flows who are HHs who are identified as HHs.
        TPR = recall = TP/(CP*1.0)
        # False Negative Rate (FPR), also known as miss rate, is the proportion of flows who are HHs who are identified as not being HHs
        FNR = FN / (CP * 1.0)
    else:
        TPR = recall = -1
        FNR = -1

    if (CN > 0):
        # True Negative Rate (TNR), also known as specificity or selectivity, is the proportion of flows who are not HHs who are identified as not being HHs.
        TNR = TN/(CN*1.0)
        # False Positive Rate (FPR), also known as fall-out, is probability of false alarm, is the proportion of flows who are not HHs who are identified as HHs
        FPR = FP / (CN * 1.0)
    else:
        TNR = -1
        FPR = -1

    if (PCP > 0):
        # Precision
        precision = TP/(PCP*1.0)
    else:
        precision = -1

    if (TPOP > 0):
        # Accuracy
        accuracy = (TP+TN)/(TPOP*1.0)
    else:
        accuracy = -1

    # F1 Score
    if ((precision>0) and (accuracy>0)):
        f1_score = 1/(((1/recall)+(1/precision))/2.0)
    else:
        f1_score = -1

    # print("     True Positive Rate (Sensitivity): " + str(100 * TPR))
    # print("     True Negative Rate (Specifity): " + str(100 * TNR))
    # print("     False Positive Rate: " + str(100*FPR))
    # print("     False Negative Rate: " + str(100 * FNR))
    # print("     Precision: " + str(100 * precision))
    # print("     Accuracy: " + str(100 * accuracy))
    # print("     F1-score: " + str(100 * f1_score))
    results = {}
    results["TPR"] = TPR
    results["TNR"] = TNR
    results["FPR"] = FPR
    results["FNR"] = FNR
    results["precision"] = precision
    results["accuracy"] = accuracy
    results["f1_score"] = f1_score

    return results

def calculate_metrics_bot(TP, FN):

    CP = TP+FN

    ## Metrics
    # True Positive Rate (TPR), also known as sensitivity or recall, is the proportion of flows who are HHs who are identified as HHs.
    if (CP > 0):
        TPR = TP/(CP*1.0)
    else:
        TPR = -1

    results = {}
    results["TPR"] = TPR

    return results