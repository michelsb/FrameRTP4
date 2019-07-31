BMV2_SWITCH_EXE = simple_switch_grpc
NO_P4 = true
P4C_ARGS = --p4runtime-file $(basename $@).p4info --p4runtime-format text

BUILD_DIR = build
LOG_DIR = logs
P4C = p4c-bm2-ss
TOPO = topologies/topology3/topology3.json

APP_DIR = p4_app

APP_FILE = rtp4app.p4
RUN_SCRIPT = run_testbed.py
source := $(APP_DIR)/$(APP_FILE)
outfile := $(APP_FILE:.p4=.json)
compiled_json := $(BUILD_DIR)/$(outfile)

APP_FILE_SCENARIO_1 = rtp4app.p4
APP_FILE_SCENARIO_2 = rtp4app_without_mon.p4
APP_FILE_SCENARIO_3 = rtp4app_mon_with_p4tables.p4
RUN_SCRIPT_EXPERIMENT = run_experiment.py
source_scenario_1 := $(APP_DIR)/$(APP_FILE_SCENARIO_1)
outfile_scenario_1 := $(APP_FILE_SCENARIO_1:.p4=.json)
compiled_json_scenario_1 := $(BUILD_DIR)/$(outfile_scenario_1)
source_scenario_2 := $(APP_DIR)/$(APP_FILE_SCENARIO_2)
outfile_scenario_2 := $(APP_FILE_SCENARIO_2:.p4=.json)
compiled_json_scenario_2 := $(BUILD_DIR)/$(outfile_scenario_2)
source_scenario_3 := $(APP_DIR)/$(APP_FILE_SCENARIO_3)
outfile_scenario_3 := $(APP_FILE_SCENARIO_3:.p4=.json)
compiled_json_scenario_3 := $(BUILD_DIR)/$(outfile_scenario_3)

# Define NO_P4 to start BMv2 without a program
ifndef NO_P4
run_args += -j $(compiled_json)
endif

run_args_experiments += -x $(compiled_json_scenario_1)
run_args_experiments += -y $(compiled_json_scenario_2)
run_args_experiments += -z $(compiled_json_scenario_3)

# Set BMV2_SWITCH_EXE to override the BMv2 target
ifdef BMV2_SWITCH_EXE
run_args += -b $(BMV2_SWITCH_EXE)
run_args_experiments += -b $(BMV2_SWITCH_EXE)
endif

all: run

run: build
	sudo python2.7 $(RUN_SCRIPT) -t $(TOPO) $(run_args)

experiment: buildtests
	sudo python2.7 $(RUN_SCRIPT_EXPERIMENT) -t $(TOPO) $(run_args_experiments)

stop:
	sudo mn -c

build: dirs $(compiled_json)

buildtests: dirs $(compiled_json_scenario_1) $(compiled_json_scenario_2) $(compiled_json_scenario_3)

$(BUILD_DIR)/%.json: $(APP_DIR)/%.p4
	$(P4C) --p4v 16 $(P4C_ARGS) -o $@ $<

dirs:
	mkdir -p $(BUILD_DIR) $(LOG_DIR)

clean: stop
	rm -f *.pcap
	rm -rf $(BUILD_DIR) $(LOG_DIR)
