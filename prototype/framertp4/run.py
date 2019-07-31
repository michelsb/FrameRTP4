import os
import definitions

if __name__ == '__main__':
    build_dir = definitions.BUILD_DIR
    logs_dir = definitions.LOG_DIR
    json_file = os.path.join(definitions.BUILD_DIR, definitions.JSON_NAME)
    db_file = os.path.join(definitions.BUILD_DIR, definitions.DB_NAME)

    # Ensure all the needed directories exist and are directories
    for dir_name in [logs_dir, build_dir]:
        if not os.path.isdir(dir_name):
            if os.path.exists(dir_name):
                raise Exception("'%s' exists and is not a directory! Program Aborted!" % dir_name)
            raise Exception("The path '%s' does not exists and is not a directory! Program Aborted! "
                            "Please perform 'make build' before run the application!" % dir_name)

    # Ensure all the needed files exist
    exists = os.path.isfile(json_file)
    if not exists:
        raise Exception(" File '%s' does not exists! Program Aborted! "
                        "Compiled files were not generated!" % json_file)
    exists = os.path.isfile(db_file)
    if not exists:
        raise Exception(" File '%s' does not exists! Program Aborted! "
                        "DB file were not generated!" % db_file)

    os.system("python3 app.py")
