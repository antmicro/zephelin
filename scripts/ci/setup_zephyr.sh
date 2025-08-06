#!/bin/bash

set -xeuo pipefail

west init -l .
west update
west patch apply
west zephyr-export
