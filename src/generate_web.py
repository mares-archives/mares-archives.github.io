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
        materials: list[list[str]],
        transcripts: list[list[str]],
        build_dir: str = "build",
        template_dir: path = "templates",
        static_dir: path = "static",
        verbose: bool = False,
        compile_tailwind: bool = False,
    ):

        self.info = info
        self.materials = materials
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

        self.paths = {
            "/": {"path": "index.html", "showHeader": False, "external": False},
            "Referats": {
                "path": "referats/index.html",
                "link": "referats/",
                "showHeader": True,
                "external": False,
            },
            "Ref": {
                "path": "ref/{}/index.html",
                "link": "ref/{}/",
                "showHeader": False,
                "external": False,
            },
            "RefMaterials": {
                "path": "ref/{}/materials/index.html",
                "link": "ref/{}/materials/",
                "showHeader": False,
                "external": False,
            },
        }

        self.env.globals["paths"] = self.paths

    def generate(self):
        self.copy_static_files()
        self.generate_refs_list()
        self.generate_ref_detail()

        self.generate_i_was_bored()

        self.generate_ref_materials()

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
        speedrun_film_lens = [
            film.get("speedrun_length")
            for film_set in film_list
            for film in film_set.values()
        ]

        info = {}
        total_seconds = 0
        for time_str in film_lens:
            hours, minutes, seconds = map(int, time_str.split(":"))
            total_seconds += hours * 3600 + minutes * 60 + seconds

        info["wasted_time"] = timedelta(seconds=total_seconds)

        total_seconds = 0
        for time_str in speedrun_film_lens:
            hours, minutes, seconds = map(int, time_str.split(":"))
            total_seconds += hours * 3600 + minutes * 60 + seconds

        info["speedrun_wasted_time"] = timedelta(seconds=total_seconds)

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
            speedrun_film_lens = [
                info["films"][f]["speedrun_length"] for f in film_list
            ]

            total_seconds = 0
            for time_str in film_lens:
                hours, minutes, seconds = map(int, time_str.split(":"))
                total_seconds += hours * 3600 + minutes * 60 + seconds

            info["total_time"] = timedelta(seconds=total_seconds)

            total_seconds = 0
            for time_str in speedrun_film_lens:
                hours, minutes, seconds = map(int, time_str.split(":"))
                total_seconds += hours * 3600 + minutes * 60 + seconds

            info["speedrun_total_time"] = timedelta(seconds=total_seconds)

            path_ref = self.paths.get("Ref").get("path").format(info["id"])

            info["films"] = info["films"].values()

            self.render_page("refDetail.html", path_ref, info=info)

    def generate_i_was_bored(self):
            self.render_page("i-was-bored.html", "i-was-bored-at-MET-classes-with-Kubosh/this-was-made-at-22:53/21.2.2025/index.html")

    def generate_ref_materials(self):
        def conv_md_ds(i: int, data: str) -> str:
            _data = str(data).split('"')
            if len(_data) == 1:
                return data

            if len(_data) % 2 == 0:
                print(f"Ref{i} - Error while converting md to html")
                return data

            tmp = ""
            for i in range(len(_data)):
                if i % 2:
                    tmp += f"<a class='font-bold'>\"{_data[i]}\"</a>"
                else:
                    tmp += f"{_data[i]}"
            return tmp

        def conv_md_strong(i: int, data: str) -> str:
            _data = str(data).split("**")
            if len(_data) == 1:
                return data

            if len(_data) % 2 == 0:
                print(f"Ref{i} - Error while converting md to html")
                return data

            tmp = ""
            for i in range(len(_data)):
                if i % 2:
                    tmp += f"<a class='font-extrabold'>{_data[i]}</a>"
                else:
                    tmp += _data[i]
            return tmp

        def conv_md_h_tags(i: int, data: str) -> str:

            tmp = []
            for d in data.split("\n"):
                if "#" in d:
                    d = (
                        "<a class='font-extrabold text-lg'>"
                        + d.replace("#", "")
                        + "</a>"
                    )
                tmp.append(d)

            return "\n".join(tmp)

        def conv_md_newline(i: int, data: str) -> str:
            data = data.replace("\n\n", "\n <br>")
            _data = []
            for d in data.split("\n"):
                _data.append(f"<p class='dark:text-gray-300 text-gray-600'>{d}</p>")
            return "".join(_data)

        def conv_markdown(i, data: str):
            data = conv_md_strong(i, data)
            data = conv_md_ds(i, data)
            data = conv_md_h_tags(i, data)
            data = conv_md_newline(i, data)

            return data

        for i, materials in enumerate(self.materials):
            path_materials = (
                self.paths.get("RefMaterials").get("path").format(f"R{i+1}")
            )

            md_materials = [conv_markdown(i, str(m)) for m in materials]

            self.render_page(
                "refMaterials.html",
                path_materials,
                refs=materials,
                md_materials=md_materials,
                info=self.info[i],
            )

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
