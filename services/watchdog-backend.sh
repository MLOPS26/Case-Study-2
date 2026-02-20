#!/bin/bash

if ! systemctl is-active --quiet backend; then
    systemctl restart backend
fi
