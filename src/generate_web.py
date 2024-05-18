import os
from datetime import timedelta
from os import path, makedirs
from typing import Union

from jinja2 import Environment, FileSystemLoader, select_autoescape, Template
from shutil import copytree
import subprocess
import logging

from src.jinja_extensions.color_extension import ColorExtension

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GenerateWeb:
    def __init__(
        self,
        info: list[dict],
        refs: list[list[str]],
        transcripts: list[list[str]],
        build_dir: str = "build",
        template_dir: path = "templates",
        static_dir: path = "static",
        verbose: bool = False,
        compile_tailwind: bool = False,
    ):

        self.info = info
        self.refs = refs
        self.transcripts = transcripts

        self.static_dir = static_dir
        self.template_dir = template_dir
        self.build_dir = build_dir
        self.verbose = verbose
        self.compile_tailwind = compile_tailwind
        if not path.exists(self.build_dir):
            makedirs(self.build_dir)

        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(["html", "jinja2"]),
            extensions=[ColorExtension],
        )

        prefix = ""
        self.paths = {
            "/": {"path": prefix+"index.html", "showHeader": False, "external": False},
            "Referats": {
                "path": prefix+"referats/index.html",
                "showHeader": True,
                "external": False,
            },
            "Ref": {
                "path": prefix+"ref/{}/index.html",
                "showHeader": False,
                "external": False,
            },
            "Transcript": {
                "path": prefix+"transcript/{}/index.html",
                "showHeader": False,
                "external": False,
            },
        }

        self.env.globals["paths"] = self.paths

    def generate(self):
        self.copy_static_files()
        self.generate_refs_list()
        self.generate_ref_detail()

        self.generate_transcript_detail()

        if self.compile_tailwind:
            self.compile_tailwind_css()

    def copy_static_files(self):
        # TODO: not working
        if self.verbose:
            logger.info(
                f"Copying static files from {self.static_dir} to {self.build_dir}"
            )

        if not path.exists(self.static_dir):
            logger.warning(f"Static directory {self.static_dir} does not exist")
            return

        copytree(self.static_dir, self.build_dir, dirs_exist_ok=True)

    def compile_tailwind_css(self):
        if self.verbose:
            logger.info("Compiling tailwindcss")

        try:
            # Assuming that your Tailwind CSS file is `./src/tailwind.css`
            # and you want to output to `./build/tailwind.css`.
            command = "npx tailwindcss -i css/style.css -o build/style.css"
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
            process.wait()
            print("Command executed successfully. Exit code:", process.returncode)

        except subprocess.CalledProcessError as e:
            print("An error occurred while executing the command. Error: ", e)

    def generate_refs_list(self):
        refs_info = self.info

        for i, r in enumerate(refs_info):
            refs_info[i]["id_name"] = f"{r['id'][1:]}. {r['name']}"

        film_list = [films for films in [i["films"] for i in refs_info]]
        film_lens = [
            film.get("length") for film_set in film_list for film in film_set.values()
        ]
        speedrunfilm_lens = [
            film.get("speedrun_length") for film_set in film_list for film in film_set.values()
        ]

        info = {}
        total_seconds = 0
        for time_str in film_lens:
            hours, minutes, seconds = map(int, time_str.split(":"))
            total_seconds += hours * 3600 + minutes * 60 + seconds

        info["wasted_time"] = timedelta(seconds=total_seconds)

        total_seconds = 0
        for time_str in speedrunfilm_lens:
            hours, minutes, seconds = map(int, time_str.split(":"))
            total_seconds += hours * 3600 + minutes * 60 + seconds

        info["wasted_speedruntime"] = timedelta(seconds=total_seconds)

        self.render_page(
            "refs.html",
            self.paths.get("Referats").get("path"),
            info=info,
            refs_info=refs_info,
        )
        self.render_page(
            "refs.html",
            self.paths.get("/").get("path"),
            info=info,
            refs_info=refs_info,
        )

    def generate_ref_detail(self):
        for i, info in enumerate(self.info):
            film_list = [films for films in info["films"]]
            film_lens = [info["films"][f]["length"] for f in film_list]
            speedrunfilm_lens = [info["films"][f]["length"] for f in film_list]

            total_seconds = 0
            for time_str in film_lens:
                hours, minutes, seconds = map(int, time_str.split(":"))
                total_seconds += hours * 3600 + minutes * 60 + seconds

            info["total_time"] = timedelta(seconds=total_seconds)

            total_seconds = 0
            for time_str in speedrunfilm_lens:
                hours, minutes, seconds = map(int, time_str.split(":"))
                total_seconds += hours * 3600 + minutes * 60 + seconds

            info["speedrun_total_time"] = timedelta(seconds=total_seconds)


            path_ref = self.paths.get("Ref").get("path").format(info["id"])

            info["films"] = info["films"].values()

            self.render_page("refDetail.html", path_ref, info=info)

    def generate_transcript_detail(self):
        print(self.transcripts)
        for i, trans in enumerate(self.transcripts):
            path_trans = self.paths.get("Transcript").get("path").format("R" + str(i))

            self.render_page("transcriptDetail.html", path_trans, trans=trans)

    def render_page(
        self, template_name: Union[str, "Template"], path_render: str, **kwargs
    ):
        template = self.env.get_template(template_name)
        full_path = os.path.join(self.build_dir, path_render)
        if not path.exists(path.dirname(full_path)):
            makedirs(path.dirname(full_path))
        try:
            with open(full_path, "w") as f:
                if self.verbose:
                    logger.info(f"Generating {path}")
                f.write(template.render(**kwargs))
        except Exception as e:
            logger.error(f"Error while generating {path_render}")
            logger.error(e)
            raise e
