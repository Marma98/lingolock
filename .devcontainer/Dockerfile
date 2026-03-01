FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH="${JAVA_HOME}/bin:${PATH}"
ENV ANDROID_SDK_ROOT=/opt/android-sdk
ENV ANDROID_NDK_HOME=/opt/android-sdk/ndk/25.2.9519653
ENV PATH="${ANDROID_SDK_ROOT}/cmdline-tools/latest/bin:${ANDROID_SDK_ROOT}/platform-tools:${PATH}"

# ── System dependencies ───────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-17-jdk \
    python3 python3-pip python3-venv python3-dev \
    git curl wget unzip zip \
    libssl-dev libffi-dev \
    zlib1g-dev libjpeg-dev libpng-dev \
    autoconf automake libtool \
    build-essential ccache \
    lld \
    && rm -rf /var/lib/apt/lists/*

# ── Python virtual environment ────────────────────────────────────────────────
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

RUN pip install --upgrade pip setuptools wheel

# ── Kivy / KivyMD / Buildozer ────────────────────────────────────────────────
RUN pip install \
    "kivy[base]==2.3.0" \
    "kivymd==1.2.0" \
    "pyjnius==1.6.1" \
    "buildozer==1.5.0" \
    "cython==3.0.10" \
    pytest

# ── Android SDK command-line tools ───────────────────────────────────────────
RUN mkdir -p ${ANDROID_SDK_ROOT}/cmdline-tools && \
    wget -q https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip \
         -O /tmp/cmdline-tools.zip && \
    unzip -q /tmp/cmdline-tools.zip -d /tmp/cmdline-tools-unzip && \
    mv /tmp/cmdline-tools-unzip/cmdline-tools ${ANDROID_SDK_ROOT}/cmdline-tools/latest && \
    rm -rf /tmp/cmdline-tools.zip /tmp/cmdline-tools-unzip

# Accept licenses and install platform + NDK
RUN yes | sdkmanager --licenses && \
    sdkmanager \
        "platform-tools" \
        "platforms;android-34" \
        "build-tools;34.0.0" \
        "ndk;25.2.9519653"

# ── Developer user ────────────────────────────────────────────────────────────
RUN useradd -ms /bin/bash developer && \
    chown -R developer:developer /opt/venv ${ANDROID_SDK_ROOT}

USER developer
WORKDIR /home/developer/app

# Pre-create .buildozer cache dir (will be volume-mounted on Windows)
RUN mkdir -p /home/developer/.buildozer

CMD ["/bin/bash"]
