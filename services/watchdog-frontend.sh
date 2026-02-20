#!/bin/bash

if ! systemctl is-active --quiet frontend; then
    systemctl restart frontend
fi
