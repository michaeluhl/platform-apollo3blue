# platform-apollo3blue: Apollo3Blue development platform for platformio.
# Copyright 2019-present NigelB
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from os.path import join, isdir
from SCons.Script import AlwaysBuild, Builder, Default, DefaultEnvironment
import platform as sys_pf

dist_sys = sys_pf.system().lower()
if dist_sys == "darwin":
    dist_sys = "macosx"

env = DefaultEnvironment()
platform = env.PioPlatform()
FRAMEWORK_DIR = platform.get_package_dir("framework-arduinoapollo3")
assert isdir(FRAMEWORK_DIR)

# A full list with the available variables
# http://www.scons.org/doc/production/HTML/scons-user.html#app-variables
env.Replace(
    AR="arm-none-eabi-ar",
    AS="arm-none-eabi-as",
    CC="arm-none-eabi-gcc",
    CXX="arm-none-eabi-g++",
    GDB="arm-none-eabi-gdb",
    OBJCOPY="arm-none-eabi-objcopy",
    RANLIB="arm-none-eabi-ranlib",
    SIZETOOL="arm-none-eabi-size",

    ARFLAGS=["rc"],
)

env.Append(
    ARFLAGS=[],
    ASFLAGS=[],
    CCFLAGS=[],
    CXXFLAGS=["-std=gnu++11"],
    LINKFLAGS=[],
    CPPDEFINES=["PART_apollo3", "AM_PACKAGE_BGA", "AM_PART_APOLLO3", "ARDUINO_ARCH_APOLLO3"],
    LIBS=[],
    BUILDERS=dict(
        ElfToBin=Builder(
            action=" ".join([
                "$OBJCOPY",
                "-O",
                "binary",
                "$SOURCES",
                "$TARGET"]),
            suffix=".bin"
        )
    )
)

#
# Target: Build executable and linkable firmware
#
target_elf = env.BuildProgram()

#
# Target: Build the .bin file
#
target_bin = env.ElfToBin(join("$BUILD_DIR", "firmware"), target_elf)

#
# Target: Upload firmware
#
upload_protocol = env.subst("$UPLOAD_PROTOCOL")

if upload_protocol.startswith('asb'):
    upload_program = join(FRAMEWORD_DIR, "tools", "uploaders", "asb", "dist", dist_sys, "asb")
    if dist_sys == "windows":
        upload_program += ".exe"
    env.Replace(
        UPLOADER=upload_program,
        UPLOADERFLAGS=["--bin", "$SOURCE",
                       "--load-address-blob", "0x20000",
                       "--magic-num", "0xCB",
                       "-o", "$TMPFILEDIR",
                       "--version", "0x0",
                       "--load-address-wired", "0xC000",
                       "-i", "6",
                       "--options", "0x1",
                       "-b", "115200",
                       "-port", "$UPLOAD_PORT",
                       "-r", "2"i,
                       "-v"],
        UPLOADCMD="$UPLOADER $UPLOADERFLAGS"
    )

elif upload_protocol.startswith('svl'):
    upload_program = join(FRAMEWORD_DIR, "tools", "uploaders", "svl", "dist", dist_sys, "svl")
    if dist_sys == "windows":
        upload_program += ".exe"
    env.Replace(
        UPLOADER=upload_program,
        UPLOADERFLAGS=["$UPLOAD_PORT",
                       "-f", "$SOURCE",
                       "-b", "921600",
                       "-v"],
        UPLOADCMD="$UPLOADER $UPLOADERFLAGS"
    )

upload_actions = [env.VerboseAction(env.AutodetectUploadPort, "Finding Upload Port..."),
                  env.VerboseAction("$UPLOADCMD", "Uploading $SOURCE")]

upload = env.Alias(["upload"], target_bin, upload_actions)
AlwaysBuild(upload)

#
# Target: Define targets
#
Default(target_bin)
