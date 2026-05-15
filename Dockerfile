FROM condaforge/miniforge3:latest

# Install FreeCAD via conda-forge (miniforge has conda-forge as default channel)
RUN mamba install -y --quiet \
        python=3.12 \
        freecad \
        pyyaml \
    && mamba clean -afy

WORKDIR /workspace

ENTRYPOINT ["freecadcmd"]
