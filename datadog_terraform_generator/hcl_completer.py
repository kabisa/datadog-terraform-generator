import io
import os
import hcl


def get_tf_files_in_path(pth):
    return [
        os.path.join(pth, o)
        for o in os.listdir(pth)
        if os.path.isfile(os.path.join(pth, o)) and o.endswith(".tf")
    ]


def write_tmp(contents):
    # useful for debugging
    with open("/tmp/tmp.txt", "w") as fl:
        fl.write(contents)


class HclCompleter:
    def __init__(self, *args, **kwargs):
        sio = io.BytesIO()
        for tf_file in get_tf_files_in_path(os.getcwd()):
            with open(tf_file, "rb") as fl:
                sio.write(fl.read())
        sio.seek(0)
        try:
            obj = hcl.load(sio)
            self.options = [f"module.{mod}" for mod in obj.get("module", {})]
            for res_type in obj.get("resource", {}):
                for res_item in obj["resource"][res_type]:
                    self.options.append(f"{res_type}.{res_item}")
        except Exception:
            # write_tmp(f"Error {er}")
            self.options = []

    def __call__(self, prefix, **kwargs):
        possibilities = [option for option in self.options if option.startswith(prefix)]
        return possibilities
