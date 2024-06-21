import sys
import yaml
import time
import shlex
import logging
import subprocess
from datetime import datetime
from jinja2 import Environment, FileSystemLoader


logging.basicConfig(level=logging.INFO,
                    handlers=[logging.StreamHandler(sys.stdout)],
                    format='%(asctime)s %(levelname)s - %(message)s',
                    datefmt='%m-%d-%y %H:%M:%S')


# render pipeline template
def get_date():
    return datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

func_dict = {
    "get_date": get_date
}

env = Environment(loader=FileSystemLoader("."))
jinja_template = env.get_template('pipeline.yaml')
jinja_template.globals.update(func_dict)
template_string = jinja_template.render()
pipeline = yaml.safe_load(template_string)

# run pipeline scripts
for script in pipeline['scripts']:
    subprocess_command = f'python src/{script}'
    args = pipeline['scripts'][script]
    if 'input' in args:
        subprocess_command += f' -i {args["input"]}'
    if 'output' in args:
        subprocess_command += f' -o {args["output"]}'

    command_line_args = shlex.split(subprocess_command)
    logging.info(subprocess_command)
    process = subprocess.Popen(command_line_args, stdout=subprocess.PIPE)
    for line in process.stdout:
        logging.info(line)

    time.sleep(10)
