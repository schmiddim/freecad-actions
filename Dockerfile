FROM condaforge/miniforge3:latest AS builder

# Install FreeCAD and dependencies into a separate environment
RUN mamba create -n freecad -y --quiet \
        python=3.12 \
        freecad \
        pyyaml \
        trimesh \
        matplotlib \
    && mamba clean -afy

# --- Runtime stage: only the conda environment, no package manager overhead ---
FROM debian:bookworm-slim

# OCI Labels for GHCR package linking
LABEL org.opencontainers.image.source="https://github.com/schmiddim/freecad-action"
LABEL org.opencontainers.image.description="FreeCAD export container for CAD Gallery"
LABEL org.opencontainers.image.licenses="MIT"

# Copy the conda environment from builder
COPY --from=builder /opt/conda/envs/freecad /opt/freecad

# Add required runtime libraries and OpenSCAD for fast thumbnail rendering
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
        libxmu6 \
        libxi6 \
        openscad \
        xvfb \
        mesa-utils \
    && rm -rf /var/lib/apt/lists/*

ENV PATH="/opt/freecad/bin:$PATH" \
    LD_LIBRARY_PATH="/opt/freecad/lib:$LD_LIBRARY_PATH"

WORKDIR /workspace

ENTRYPOINT ["freecadcmd"]
