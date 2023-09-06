#!/usr/bin/env python3

#
# This file is part of LiteX-Boards.
#
# Copyright (c) 2023 Icenowy Zheng <uwu@icenowy.me>
# Copyright (c) 2023 wonderfullook <123hyx456@gmail.com>
# SPDX-License-Identifier: BSD-2-Clause

from migen import *
from migen.genlib.resetsync import AsyncResetSynchronizer

from litex.gen import *

from litex.soc.cores.clock.gowin_gw5a import GW5APLL
from litex.soc.integration.soc_core import *
from litex.soc.integration.soc import SoCRegion
from litex.soc.integration.builder import *
from litex.soc.cores.led import LedChaser, WS2812

from litedram.modules import AS4C32M16
from litedram.phy import GENSDRPHY, HalfRateGENSDRPHY
from litex.build.io import DDROutput

from litex_boards.platforms import sipeed_tang_primer_25k

# CRG ----------------------------------------------------------------------------------------------

class _CRG(LiteXModule):
    def __init__(self, platform, sys_clk_freq, with_sdram=False):
        self.rst      = Signal()
        self.cd_sys   = ClockDomain()
        self.cd_por   = ClockDomain()
        if with_sdram:
            self.cd_sys_ps = ClockDomain()

        # Clk
        self.clk50 = platform.request("clk50")
        rst = platform.request("rst")

        # Power on reset
        por_count = Signal(16, reset=2**16-1)
        por_done  = Signal()
        self.comb += self.cd_por.clk.eq(self.clk50)
        self.comb += por_done.eq(por_count == 0)
        self.sync.por += If(~por_done, por_count.eq(por_count - 1))

        # PLL
        self.pll = pll = GW5APLL(devicename=platform.devicename, device=platform.device)
        self.comb += pll.reset.eq(~por_done | self.rst | rst)
        pll.register_clkin(self.clk50, 50e6)
        pll.create_clkout(self.cd_sys, sys_clk_freq)
        if with_sdram:
            pll.create_clkout(self.cd_sys_ps, sys_clk_freq, phase=90)

        # SDRAM clock
        if with_sdram:
            sdram_clk = ClockSignal("sys_ps")
            self.specials += DDROutput(1, 0, platform.request("sdram_clock"), sdram_clk)

# BaseSoC ------------------------------------------------------------------------------------------

class BaseSoC(SoCCore):
    def __init__(self, sys_clk_freq=50e6,
        with_sdram          = False,
        with_led_chaser     = True,
        with_buttons        = True,
        **kwargs):

        platform = sipeed_tang_primer_25k.Platform(toolchain="gowin")

        # CRG --------------------------------------------------------------------------------------
        self.crg = _CRG(platform, sys_clk_freq, with_sdram=with_sdram)

        # SoCCore ----------------------------------------------------------------------------------
        SoCCore.__init__(self, platform, sys_clk_freq, ident="LiteX SoC on Tang Primer 25K", **kwargs)

        # Leds -------------------------------------------------------------------------------------
        if with_led_chaser:
            self.leds = LedChaser(
                pads         = platform.request_all("led"),
                sys_clk_freq = sys_clk_freq
            )

        # SDR SDRAM --------------------------------------------------------------------------------
        if with_sdram and not self.integrated_main_ram_size:
            self.sdrphy = GENSDRPHY(platform.request("sdram"), sys_clk_freq)
            self.add_sdram("sdram",
                phy           = self.sdrphy,
                module        = AS4C32M16(sys_clk_freq, "1:1"),
                l2_cache_size = kwargs.get("l2_size", 8192)
            )

# Build --------------------------------------------------------------------------------------------

def main():
    from litex.build.parser import LiteXArgumentParser
    parser = LiteXArgumentParser(platform=sipeed_tang_primer_25k.Platform, description="LiteX SoC on Tang primer 25K.")
    parser.add_target_argument("--flash",           action="store_true",      help="Flash Bitstream.")
    parser.add_target_argument("--sys-clk-freq",    default=50e6, type=float, help="System clock frequency.")
    parser.add_target_argument("--with-sdram",      action="store_true",      help="Enable optional SDRAM module.")
    args = parser.parse_args()

    soc = BaseSoC(
        sys_clk_freq        = args.sys_clk_freq,
        with_sdram          = args.with_sdram,
        **parser.soc_argdict
    )

    builder = Builder(soc, **parser.builder_argdict)
    if args.build:
        builder.build(**parser.toolchain_argdict)

    if args.load:
        prog = soc.platform.create_programmer()
        prog.load_bitstream(builder.get_bitstream_filename(mode="sram"))

    if args.flash:
        prog = soc.platform.create_programmer()
        prog.flash(0, builder.get_bitstream_filename(mode="flash", ext=".fs"), external=True)

if __name__ == "__main__":
    main()
