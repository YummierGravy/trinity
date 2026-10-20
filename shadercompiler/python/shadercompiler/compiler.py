# Copyright (c) 2023 CCP ehf.
import os
import subprocess
import sys

BUILDER_DIR = os.path.dirname(os.path.abspath(__file__))

ENGINE_TOOLSET = 'v145'

if sys.platform == 'win32':
    ENGINE_PLATFORM_FOLDER = os.path.join('Windows', 'x64', ENGINE_TOOLSET)
    COMPILER_NAME = 'ShaderCompiler.exe'
elif sys.platform == 'darwin':
    ENGINE_PLATFORM_FOLDER = os.path.join('macOS', 'universal', 'AppleClang')
    COMPILER_NAME = 'ShaderCompiler'
else:
    raise RuntimeError('unsupported platform')


def _find_compiler():
    """The ShaderCompiler the carbon engine ships in its bin folder.

    This package is imported either from the engine's own tree, <engine>/<platform folder>/python/shadercompiler, where
    the compiler is next to the python folder, or from a copy a branch made of it (updateBinaries copies it into
    packages/), where the engine is in the branch's vendor/carbon.
    """
    candidates = [os.path.join(BUILDER_DIR, '..', '..', 'bin', COMPILER_NAME)]
    directory = BUILDER_DIR
    while True:
        candidates.append(os.path.join(directory, 'vendor', 'carbon', ENGINE_PLATFORM_FOLDER, 'bin', COMPILER_NAME))
        parent = os.path.dirname(directory)
        if parent == directory:  # reached the filesystem root
            break
        directory = parent
    for candidate in candidates:
        if os.path.isfile(candidate):
            return os.path.abspath(candidate)
    raise RuntimeError('could not locate %s in the engine from %s' % (COMPILER_NAME, BUILDER_DIR))


COMPILER_PATH = _find_compiler()


class GLESExtensionOption(object):
    WARN = 'w'
    ENABLE = 'e'
    DISABLE = 'd'


CompilerError = subprocess.CalledProcessError


def compile_shader(effect_path, output_path=None, platform=None, shader_model=None, threads=None, warnings=True,
                   defines=None, optimizations=3, avoid_flow_control=False):
    if output_path is None:
        if platform is None or shader_model is None:
            raise RuntimeError('cannot have both output_path and platform or shader_model None')
        output_path = paths.get_compiled_path(effect_path, shader_model, platform)
    try:
        os.makedirs(os.path.dirname(output_path))
    except OSError:
        pass
    args = [COMPILER_PATH, '/single', '/O%s' % optimizations]
    if threads is not None:
        args.extend(('/threads', str(threads)))
    if not warnings:
        args.append('/no_warnings')
    if platform is not None:
        args.extend(('/define', 'PLATFORM', str(platform)))
    if shader_model is not None:
        args.extend(('/define', 'SHADERMODEL', str(shader_model)))
    for name, value in (defines or {}).items():
        args.extend(('/define', name, str(value)))
    if avoid_flow_control:
        args.append('/Gfa')
    args.append(effect_path)
    args.append(output_path)
    print(args)
    return subprocess.check_output(args)
