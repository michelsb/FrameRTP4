import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(ROOT_DIR, '..' )
ROOT_DIR = os.path.join(ROOT_DIR, '..' )
BASE_DIR = os.path.join(ROOT_DIR, '..' )
DATASET_DIR = os.path.join(BASE_DIR, 'datasets')

metrics = ["fpr","recall","precision","accuracy","f1-score"]
factors = ["time_window"]
metrics_position = {"fpr":10,"recall":8,"precision":12,"accuracy":13,"f1-score":14}
metrics_title = {"fpr":"False Positive Rate (%)","recall":"Recall (%)","precision":"Precision (%)","accuracy":"Accuracy (%)","f1-score":"F1-Score (%)"}
metrics_properties= {
    "fpr":{"title":"False Positive Rate","marker":">","color":"red"},
    "recall":{"title":"Recall","marker":"^","color":"green"},
    "precision":{"title":"Precision","marker":"s","color":"blue"},
    "accuracy":{"title":"Accuracy","marker":"x","color":"cyan"},
    "f1-score":{"title":"F1-Score","marker":"*","color":"magenta"}
}

# 0,1%
#bound = 0.001
# 0,01%
#bound = 0.0001

#bounds = [0.0001,0.001,0.01]
array_bound = [0.001]

# window of 20 seconds (to clean up the sketch)
#array_num_chunks = [10,9,8,7,6,5,4,3,2,1]
#array_num_chunks = [10,8,6,4,2,1]

#array_time_window = [30,60,90,120]
#array_pkts_to_start = [1000,3000,5000]

array_time_window = [30,60,90,120,150]
array_pkts_to_start = [1000]

flow_id = ["SrcIP", "DstIP", "Proto", "SrcPort", "DstPort"]
#flow_id = ["SrcIP"]
colors = (0, 0, 0)