source .venv/bin/activate
source $HOME/.local/bin/env
export PATH=$PATH:/opt/renode
source zpl_env.sh

if [ -d renode_portable ]; then
  export PYRENODE_PATH=$(realpath renode_portable)
  export PYRENODE_BIN=$(realpath renode_portable/renode)
  export PYRENODE_RUNTIME=coreclr
  export PATH=$PATH:$(realpath renode_portable/)
fi

if [ -d /opt/renode ]; then
  export PYRENODE_PATH=/opt/renode
fi
