#!/usr/bin/env bash

_joi() {
    local cur prev words cword
    _init_completion || return

    local commands="setup install migrate seed admin server check reset update help version"
    local options="--help --version --yes --no-color --verbose --quiet --debug --port --clear --seed --no-seed --admin --no-admin --skip-migrations"

    if [[ ${cword} -eq 1 ]]; then
        COMPREPLY=($(compgen -W "${commands}" -- "${cur}"))
        return
    fi

    case "${words[1]}" in
        server)
            if [[ "${prev}" == "--port" || "${prev}" == "-p" ]]; then
                return
            fi
            COMPREPLY=($(compgen -W "${options} --port" -- "${cur}"))
            ;;
        seed)
            COMPREPLY=($(compgen -W "${options} --clear" -- "${cur}"))
            ;;
        setup)
            COMPREPLY=($(compgen -W "${options} --seed --no-seed --admin --no-admin --skip-migrations" -- "${cur}"))
            ;;
        -*)
            COMPREPLY=($(compgen -W "${commands}" -- "${cur}"))
            ;;
    esac
}

complete -F _joi joi