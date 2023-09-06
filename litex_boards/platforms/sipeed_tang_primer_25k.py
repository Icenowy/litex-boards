#
# This file is part of LiteX-Boards.
#
# Copyright (c) 2023 Icenowy Zheng <uwu@icenowy.me>
# Copyright (c) 2023 wonderfullook <123hyx456@gmail.com>
# SPDX-License-Identifier: BSD-2-Clause

from migen import *

from litex.build.generic_platform import *
from litex.build.gowin.platform import GowinPlatform
from litex.build.gowin.programmer import GowinProgrammer
from litex.build.openfpgaloader import OpenFPGALoader


# IOs ----------------------------------------------------------------------------------------------

_io = [
    # Clk / Rst.
    ("clk50",  0, Pins("E2"), IOStandard("LVCMOS33")),
    ("rst",    0, Pins("H11"), IOStandard("LVCMOS33"), Misc("PULL_MODE=DOWN")),

    # Serial.
    ("serial", 0,
        Subsignal("rx", Pins("B3")),
        Subsignal("tx", Pins("C3")),
        IOStandard("LVCMOS33")
    ),
    
    ("led", 0,  Pins( "L6"), IOStandard("LVCMOS33")),
    
    ("sdram_clock", 0, Pins("E3"), IOStandard("LVCMOS33")),
    ("sdram", 0,
        Subsignal("a",   Pins(
            "F6 F7 J10 J11 K7 H2 H1 H4 G4 J2",
            "J8 J1 D1")),
        Subsignal("dq",  Pins(
            "K2 K1 L1 L2 K4 J4 G1 G2 E1 A1",
            "F2 F1 B2 C2 L4 L3")),
        Subsignal("ba",    Pins("L9 K8")),
        Subsignal("cas_n", Pins("K10")),
        Subsignal("cs_n",  Pins("K9")),
        Subsignal("ras_n", Pins("L10")),
        Subsignal("we_n",  Pins("J7")),
        IOStandard("LVCMOS33"),
    ),
]

_connectors = [
    
]

# Platform -----------------------------------------------------------------------------------------

class Platform(GowinPlatform):
    default_clk_name   = "clk50"
    default_clk_period = 1e9/50e6

    def __init__(self, dock="standard", toolchain="gowin"):
        GowinPlatform.__init__(self, "GW5A-LV25MG121NES", _io, toolchain=toolchain, devicename="GW5A-25A")

        self.toolchain.options["use_sspi_as_gpio"] = 1
        self.toolchain.options["use_cpu_as_gpio"]  = 1
        self.toolchain.options["use_i2c_as_gpio"]  = 1
        self.toolchain.options["rw_check_on_ram"]  = 1
        self.toolchain.options["bit_security"]     = 0
        self.toolchain.options["bit_encrypt"]      = 0
        self.toolchain.options["bit_compress"]     = 0
        self.toolchain.options["ireg_in_iob"]      = 0
        self.toolchain.options["oreg_in_iob"]      = 0
        self.toolchain.options["ioreg_in_iob"]     = 0
        self.toolchain.options["reg_in_iob"]       = 0

    def create_programmer(self, kit="openfpgaloader"):
        return OpenFPGALoader(cable="ft2232")

    def do_finalize(self, fragment):
        GowinPlatform.do_finalize(self, fragment)
        self.add_period_constraint(self.lookup_request("clk50", loose=True), 1e9/50e6)
