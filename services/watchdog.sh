#!/bin/bash

if ! systemctl is-active --quiet backend; then
    systemctl restart backend
fi

if ! systemctl is-active --quiet frontend; then
    systemctl restart frontend
fi
