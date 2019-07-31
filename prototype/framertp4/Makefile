BUILD_DIR = build
LOG_DIR = logs
APP_DIR = rtp4app
APP_NAME = rtp4app

P4C_ARGS = --p4runtime-file $(BUILD_DIR)/$(APP_NAME).p4info --p4runtime-format text

P4C = p4c-bm2-ss
BUILD_SCRIPT = build.py
RUN_SCRIPT = run.py

SOURCE_FILE := $(APP_DIR)/$(APP_NAME).p4
OUTPUT_FILE := $(BUILD_DIR)/$(APP_NAME).json

compiled_json := $(OUTPUT_FILE)
build_args += -j $(compiled_json)

all: build

build: compile
	sudo python3 $(BUILD_SCRIPT) $(build_args)

compile: dirs $(compiled_json)

$(OUTPUT_FILE): $(SOURCE_FILE)
	$(P4C) --p4v 16 $(P4C_ARGS) -o $@ $<

dirs:
	mkdir -p $(BUILD_DIR) $(LOG_DIR)

run:
	sudo python3 $(RUN_SCRIPT)

clean:
	rm -rf $(BUILD_DIR) $(LOG_DIR)
