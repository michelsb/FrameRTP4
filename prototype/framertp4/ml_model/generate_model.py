#from sklearn.externals import joblib
import joblib
import pandas as pd
import numpy as np
import datetime

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error,accuracy_score,confusion_matrix,classification_report

import os, sys
parentPath = os.path.abspath("..")
if parentPath not in sys.path:
    sys.path.insert(0, parentPath)

def save_model_file(model,name):
    joblib.dump(model, name+".joblib")

def load_model_file(name):
    clf = joblib.load(name+".joblib")
    return clf

def read_csv_file():
    print("# " + str(datetime.datetime.now()) + " - Reading CSV...")
    #df = pd.read_csv("csv/final.csv", sep='\t', header=0, usecols = ['hdrDesc','numHdrs', 'srcIP', 'dstIP', 'srcPort', 'dstPort', 'l4Proto','numPktsSnt','numPktsRcvd','numBytesSnt','numBytesRcvd','minPktSz','maxPktSz','avePktSize','stdPktSize','minIAT','maxIAT','aveIAT','stdIAT','pktps','bytps','pktAsm','bytAsm','tcpFStat','ipMindIPID','ipMaxdIPID','ipMinTTL','ipMaxTTL','ipTTLChg','ipTOS','ipFlags','file_name','type'],converters={"tcpFStat": lambda x: int(x, 16),"ipTOS": lambda x: int(x, 16),"ipFlags": lambda x: int(x, 16)})
    df = pd.read_csv("csv/final.csv", sep='\t', header=0,
                     usecols=['hdrDesc', 'numHdrs', 'srcIP', 'dstIP', 'srcPort', 'dstPort', 'l4Proto', 'numPktsSnt',
                              'numPktsRcvd', 'numBytesSnt', 'numBytesRcvd', 'pktps', 'bytps', 'file_name', 'type'])
    print("# " + str(datetime.datetime.now()) + " - CSV loaded inside a dataframe...")

    print("# " + str(datetime.datetime.now()) + " - Applying filters...")
    df = df.replace('4;3', '4')
    df = df.replace('3;4', '3')
    df = df[df['hdrDesc'].str.contains("arp|ipv6")==False].reset_index(drop=True)
    df = df.drop('hdrDesc', axis=1)
    print("# " + str(datetime.datetime.now()) + " - Filters applied...")

    return df

def generate_model():
    classifier_names = [
        #"Nearest Neighbors",
        #"Linear SVM",
        #"RBF SVM",
        #"Gaussian Process",
        #"Decision Tree",
        "Random Forest",
        #"Neural Net",
        #"AdaBoost",
        #"Naive Bayes",
        #"QDA"
    ]

    classifiers_instances = [
        #KNeighborsClassifier(3),
        #SVC(kernel="linear", C=0.025),
        #SVC(gamma=2, C=1),
        #GaussianProcessClassifier(1.0 * RBF(1.0)),
        #DecisionTreeClassifier(max_depth=5),
        RandomForestClassifier(max_depth=5, n_estimators=10, max_features=1),
        #MLPClassifier(alpha=1),
        #AdaBoostClassifier(),
        #GaussianNB(),
        #QuadraticDiscriminantAnalysis()
    ]

    df = read_csv_file()

    y = df['type']
    X = df.drop('type', axis=1).drop('file_name', axis=1)\
        .drop('srcIP', axis=1).drop('dstIP', axis=1)\
        .drop('srcPort', axis=1).drop('dstPort', axis=1)\
        .drop('numHdrs', axis=1).drop('l4Proto', axis=1)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    # iterate over classifiers
    for name, clf in zip(classifier_names, classifiers_instances):
        print("# ALGORITHM: " + name)

        #print("1 - Without Cross Validation")
        clf.fit(X_train, y_train)
        preds = clf.predict(X_test)
        print("1.1 - Accuracy: " + str(accuracy_score(y_test, preds)))
        print("1.2 - Confusion Matrix:")
        print(confusion_matrix(y_test, preds))
        print("1.3 - Classification Report:")
        print(classification_report(y_test, preds))
        save_model_file(clf, name)

def classifier(df):
    name = "Random Forest"
    clf = load_model_file(name)

    X = df.drop('type', axis=1).drop('file_name', axis=1).drop('srcIP', axis=1).drop('dstIP', axis=1).drop('srcPort',axis=1).drop('dstPort', axis=1)

    preds = clf.predict(X)
    indexes = np.where(preds == 0)
    results = df.loc[indexes[0],["srcIP", "srcPort", "dstIP", "dstPort","l4Proto"]]

    return results

# def pattern_generator(df):
#     num_flows = len(df.index)
#     generate_flows_with_wildcards(df)
#     df = df[["srcIP", "srcPort", "dstIP", "dstPort", "l4Proto"]].drop_duplicates()
#     print("Number of Original Flows: " + str(num_flows))
#     print("Number of Flows with Wildcards: " + str(len(df.index)))
#
#     return df
#
# def create_malicious_rules(rules):
#     print("# " + str(datetime.datetime.now()) + " - Connecting to controller servers...")
#
#     idps_client = IDPSClientController()
#     idps_client.startClientController("server.txt")
#
#     print("# " + str(datetime.datetime.now()) + " - Start to create malicious rules...")
#
#     for index, row in df.iterrows():
#         idps_client.writeMaliciousRule(str(row["l4Proto"]), row["srcIP"], row["dstIP"], row["srcPort"], row["dstPort"])

generate_model()

# df = read_csv_file()
# malicious_flows = classifier(df)
# malicious_rules = pattern_generator(malicious_flows)
# create_malicious_rules(malicious_rules)
