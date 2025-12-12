from dataReader import PSTTReader
import logging
import pathlib
import os
import yaml
import torch
from tools import tools

folder = pathlib.Path(__file__).parent.resolve()

def load_cfg(path: str):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def setup_logger(logger_name, log_file, level=logging.INFO):
    l = logging.getLogger(logger_name)
    formatter = logging.Formatter('%(asctime)s : %(message)s')
    fileHandler = logging.FileHandler(log_file, mode='w')
    fileHandler.setFormatter(formatter)
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(formatter)

    l.setLevel(level)
    l.addHandler(fileHandler)
    l.addHandler(streamHandler) 

def startup(data_folder, output_folder, fileName):
    pname = fileName.split('.xml')[0]
    # 设置log的格式
    os.makedirs(f"{output_folder}/{pname}", exist_ok=True)
    setup_logger(pname, f"{output_folder}/{pname}/{pname}.log")
    logger = logging.getLogger(pname)
    file = f"{data_folder}/{fileName}"
    reader = PSTTReader(file)
    return reader, logger

def main(config):
    if config['method']['name'] == "Random":
        output_folder = config['config']['output']
        quickrun = config["method"].get("quickrun", False)
        from MARL.Random.train import train
        if config['data']['isthrough']:
            data_folder = config["data"]["folder"]
            for fileName in os.listdir(data_folder):
                if fileName.endswith('.xml'):
                    reader, logger = startup(data_folder, output_folder, fileName)
                    Tools = tools(logger, config)
                    train(reader, logger, Tools, output_folder, fileName, config, quickrun)
        else:
            data_folder = config["data"]["folder"]
            fileName = config["data"]["file"]
            reader, logger = startup(data_folder, output_folder, fileName)
            Tools = tools(logger, config)
            train(reader, logger, Tools, output_folder, fileName, config, quickrun)
    elif config['method']['name'] == "PMAPPO":
        output_folder = config['config']['output']
        quickrun = config["method"].get("quickrun", False)
        from MARL.PMAPPO.train import train
        if config['data']['isthrough']:
            data_folder = config["data"]["folder"]
            for fileName in os.listdir(data_folder):
                if fileName.endswith('.xml'):
                    reader, logger = startup(data_folder, output_folder, fileName)
                    Tools = tools(logger, config)
                    train(reader, logger, Tools, output_folder, fileName, config, quickrun)
        else:
            data_folder = config["data"]["folder"]
            fileName = config["data"]["file"]
            reader, logger = startup(data_folder, output_folder, fileName)
            Tools = tools(logger, config)
            train(reader, logger, Tools, output_folder, fileName, config, quickrun)
    elif config['method']['name'] == "RPMAPPO":
        output_folder = config['config']['output']
        quickrun = config["method"].get("quickrun", False)
        from MARL.RPMAPPO.train import train
        if config['data']['isthrough']:
            data_folder = config["data"]["folder"]
            for fileName in os.listdir(data_folder):
                if fileName.endswith('.xml'):
                    reader, logger = startup(data_folder, output_folder, fileName)
                    Tools = tools(logger, config)
                    train(reader, logger, Tools, output_folder, fileName, config, quickrun)
        else:
            data_folder = config["data"]["folder"]
            fileName = config["data"]["file"]
            reader, logger = startup(data_folder, output_folder, fileName)
            Tools = tools(logger, config)
            train(reader, logger, Tools, output_folder, fileName, config, quickrun)

if __name__ == "__main__":
    # Load configuration
    config = load_cfg(f"{folder}/config.yaml")
    device = torch.device("cuda" if config['device'] == "gpu" and torch.cuda.is_available() else "cpu")
    main(config)