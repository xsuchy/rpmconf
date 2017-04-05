# -*- coding: utf-8 -*-

from distutils.core import setup

setup(name = "rpmconf",
      packages = ["rpmconf"],
      version = "1.0.19",
      description = "Handle rpmnew and rpmsave files",
      author = "Igor Gnatenko",
      author_email = "i.gnatenko.brain@gmail.com",
      maintainer = "Miroslav Suchý",
      maintainer_email = "msuchy@redhat.com",
      url = "https://github.com/xsuchy/rpmconf",
      keywords = ["rpm"],
      scripts = ["bin/rpmconf"]
     )
