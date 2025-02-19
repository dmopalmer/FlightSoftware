from enum import IntEnum, unique
import time

@unique
class Reg(IntEnum):
    SILICONREVISION = 0x000
    SCRATCH = 0x001
    PWRMODE = 0x002
    POWSTAT = 0x003
    POWSTICKYSTAT = 0x004
    POWIRQMASK = 0x005
    IRQMASK1 = 0x006
    IRQMASK0 = 0x007
    RADIOEVENTMASK1 = 0x008
    RADIOEVENTMASK0 = 0x009
    IRQINVERSION1 = 0x00A
    IRQINVERSION0 = 0x00B
    IRQREQUEST1 = 0x00C
    IRQREQUEST0 = 0x00D
    RADIOEVENTREQ1 = 0x00E
    RADIOEVENTREQ0 = 0x00F
    MODULATION = 0x010
    ENCODING = 0x011
    FRAMING = 0x012
    CRCINIT3 = 0x014
    CRCINIT2 = 0x015
    CRCINIT1 = 0x016
    CRCINIT0 = 0x017
    FEC = 0x018
    FECSYNC = 0x019
    FECSTATUS = 0x01A
    RADIOSTATE = 0x01C
    XTALSTATUS = 0x01D
    PINSTATE = 0x020
    PINFUNCSYSCLK = 0x021
    PINFUNCDCLK = 0x022
    PINFUNCDATA = 0x023
    PINFUNCIRQ = 0x024
    PINFUNCANTSEL = 0x025
    PINFUNCPWRAMP = 0x026
    PWRAMP = 0x027
    FIFOSTAT = 0x028
    FIFODATA = 0x029
    FIFOCOUNT1 = 0x02A
    FIFOCOUNT0 = 0x02B
    FIFOFREE1 = 0x02C
    FIFOFREE0 = 0x02D
    FIFOTHRESH1 = 0x02E
    FIFOTHRESH0 = 0x02F
    PLLLOOP = 0x030
    PLLCPI = 0x031
    PLLVCODIV = 0x032
    PLLRANGINGA = 0x033
    FREQA3 = 0x034
    FREQA2 = 0x035
    FREQA1 = 0x036
    FREQA0 = 0x037
    PLLLOOPBOOST = 0x038
    PLLCPIBOOST = 0x039
    PLLRANGINGB = 0x03B
    FREQB3 = 0x03C
    FREQB2 = 0x03D
    FREQB1 = 0x03E
    FREQB0 = 0x03F
    RSSI = 0x040
    BGNDRSSI = 0x041
    DIVERSITY = 0x042
    AGCCOUNTER = 0x043
    TRKDATARATE2 = 0x045
    TRKDATARATE1 = 0x046
    TRKDATARATE0 = 0x047
    TRKAMPL1 = 0x048
    TRKAMPL0 = 0x049
    TRKPHASE1 = 0x04A
    TRKPHASE0 = 0x04B
    TRKRFFREQ2 = 0x04D
    TRKRFFREQ1 = 0x04E
    TRKRFFREQ0 = 0x04F
    TRKFREQ1 = 0x050
    TRKFREQ0 = 0x051
    TRKFSKDEMOD1 = 0x052
    TRKFSKDEMOD0 = 0x053
    TRKAFSKDEMOD1 = 0x054
    TRKAFSKDEMOD0 = 0x055
    TIMER2 = 0x059
    TIMER1 = 0x05A
    TIMER0 = 0x05B
    WAKEUPTIMER1 = 0x068
    WAKEUPTIMER0 = 0x069
    WAKEUP1 = 0x06A
    WAKEUP0 = 0x06B
    WAKEUPFREQ1 = 0x06C
    WAKEUPFREQ0 = 0x06D
    WAKEUPXOEARLY = 0x06E
    IFFREQ1 = 0x100
    IFFREQ0 = 0x101
    DECIMATION = 0x102
    RXDATARATE2 = 0x103
    RXDATARATE1 = 0x104
    RXDATARATE0 = 0x105
    MAXDROFFSET2 = 0x106
    MAXDROFFSET1 = 0x107
    MAXDROFFSET0 = 0x108
    MAXRFOFFSET2 = 0x109
    MAXRFOFFSET1 = 0x10A
    MAXRFOFFSET0 = 0x10B
    FSKDMAX1 = 0x10C
    FSKDMAX0 = 0x10D
    FSKDMIN1 = 0x10E
    FSKDMIN0 = 0x10F
    AFSKSPACE1 = 0x110
    AFSKSPACE0 = 0x111
    AFSKMARK1 = 0x112
    AFSKMARK0 = 0x113
    AFSKCTRL = 0x114
    AMPLFILTER = 0x115
    FREQUENCYLEAK = 0x116
    RXPARAMSETS = 0x117
    RXPARAMCURSET = 0x118
    AGCGAIN0 = 0x120
    AGCTARGET0 = 0x121
    AGCAHYST0 = 0x122
    AGCMINMAX0 = 0x123
    TIMEGAIN0 = 0x124
    DRGAIN0 = 0x125
    PHASEGAIN0 = 0x126
    FREQUENCYGAINA0 = 0x127
    FREQUENCYGAINB0 = 0x128
    FREQUENCYGAINC0 = 0x129
    FREQUENCYGAIND0 = 0x12A
    AMPLITUDEGAIN0 = 0x12B
    FREQDEV10 = 0x12C
    FREQDEV00 = 0x12D
    FOURFSK0 = 0x12E
    BBOFFSRES0 = 0x12F
    AGCGAIN1 = 0x130
    AGCTARGET1 = 0x131
    AGCAHYST1 = 0x132
    AGCMINMAX1 = 0x133
    TIMEGAIN1 = 0x134
    DRGAIN1 = 0x135
    PHASEGAIN1 = 0x136
    FREQUENCYGAINA1 = 0x137
    FREQUENCYGAINB1 = 0x138
    FREQUENCYGAINC1 = 0x139
    FREQUENCYGAIND1 = 0x13A
    AMPLITUDEGAIN1 = 0x13B
    FREQDEV11 = 0x13C
    FREQDEV01 = 0x13D
    FOURFSK1 = 0x13E
    BBOFFSRES1 = 0x13F
    AGCGAIN2 = 0x140
    AGCTARGET2 = 0x141
    AGCAHYST2 = 0x142
    AGCMINMAX2 = 0x143
    TIMEGAIN2 = 0x144
    DRGAIN2 = 0x145
    PHASEGAIN2 = 0x146
    FREQUENCYGAINA2 = 0x147
    FREQUENCYGAINB2 = 0x148
    FREQUENCYGAINC2 = 0x149
    FREQUENCYGAIND2 = 0x14A
    AMPLITUDEGAIN2 = 0x14B
    FREQDEV12 = 0x14C
    FREQDEV02 = 0x14D
    FOURFSK2 = 0x14E
    BBOFFSRES2 = 0x14F
    AGCGAIN3 = 0x150
    AGCTARGET3 = 0x151
    AGCAHYST3 = 0x152
    AGCMINMAX3 = 0x153
    TIMEGAIN3 = 0x154
    DRGAIN3 = 0x155
    PHASEGAIN3 = 0x156
    FREQUENCYGAINA3 = 0x157
    FREQUENCYGAINB3 = 0x158
    FREQUENCYGAINC3 = 0x159
    FREQUENCYGAIND3 = 0x15A
    AMPLITUDEGAIN3 = 0x15B
    FREQDEV13 = 0x15C
    FREQDEV03 = 0x15D
    FOURFSK3 = 0x15E
    BBOFFSRES3 = 0x15F
    MODCFGF = 0x160
    FSKDEV2 = 0x161
    FSKDEV1 = 0x162
    FSKDEV0 = 0x163
    MODCFGA = 0x164
    TXRATE2 = 0x165
    TXRATE1 = 0x166
    TXRATE0 = 0x167
    TXPWRCOEFFA1 = 0x168
    TXPWRCOEFFA0 = 0x169
    TXPWRCOEFFB1 = 0x16A
    TXPWRCOEFFB0 = 0x16B
    TXPWRCOEFFC1 = 0x16C
    TXPWRCOEFFC0 = 0x16D
    TXPWRCOEFFD1 = 0x16E
    TXPWRCOEFFD0 = 0x16F
    TXPWRCOEFFE1 = 0x170
    TXPWRCOEFFE0 = 0x171
    PLLVCOI = 0x180
    PLLVCOIR = 0x181
    PLLLOCKDET = 0x182
    PLLRNGCLK = 0x183
    XTALCAP = 0x184
    BBTUNE = 0x188
    BBOFFSCAP = 0x189
    PKTADDRCFG = 0x200
    PKTLENCFG = 0x201
    PKTLENOFFSET = 0x202
    PKTMAXLEN = 0x203
    PKTADDR3 = 0x204
    PKTADDR2 = 0x205
    PKTADDR1 = 0x206
    PKTADDR0 = 0x207
    PKTADDRMASK3 = 0x208
    PKTADDRMASK2 = 0x209
    PKTADDRMASK1 = 0x20A
    PKTADDRMASK0 = 0x20B
    MATCH0PAT3 = 0x210
    MATCH0PAT2 = 0x211
    MATCH0PAT1 = 0x212
    MATCH0PAT0 = 0x213
    MATCH0LEN = 0x214
    MATCH0MIN = 0x215
    MATCH0MAX = 0x216
    MATCH1PAT1 = 0x218
    MATCH1PAT0 = 0x219
    MATCH1LEN = 0x21C
    MATCH1MIN = 0x21D
    MATCH1MAX = 0x21E
    TMGTXBOOST = 0x220
    TMGTXSETTLE = 0x221
    TMGRXBOOST = 0x223
    TMGRXSETTLE = 0x224
    TMGRXOFFSACQ = 0x225
    TMGRXCOARSEAGC = 0x226
    TMGRXAGC = 0x227
    TMGRXRSSI = 0x228
    TMGRXPREAMBLE1 = 0x229
    TMGRXPREAMBLE2 = 0x22A
    TMGRXPREAMBLE3 = 0x22B
    RSSIREFERENCE = 0x22C
    RSSIABSTHR = 0x22D
    BGNDRSSIGAIN = 0x22E
    BGNDRSSITHR = 0x22F
    PKTCHUNKSIZE = 0x230
    PKTMISCFLAGS = 0x231
    PKTSTOREFLAGS = 0x232
    PKTACCEPTFLAGS = 0x233
    GPADCCTRL = 0x300
    GPADCPERIOD = 0x301
    GPADC13VALUE1 = 0x308
    GPADC13VALUE0 = 0x309
    LPOSCCONFIG = 0x310
    LPOSCSTATUS = 0x311
    LPOSCKFILT1 = 0x312
    LPOSCKFILT0 = 0x313
    LPOSCREF1 = 0x314
    LPOSCREF0 = 0x315
    LPOSCFREQ1 = 0x316
    LPOSCFREQ0 = 0x317
    LPOSCPER1 = 0x318
    LPOSCPER0 = 0x319
    DACVALUE1 = 0x330
    DACVALUE0 = 0x331
    DACCONFIG = 0x332
    TUNE_F00 = 0xF00
    POWCTRL1 = 0xF08
    TUNE_F0C = 0xF0C
    REF = 0xF0D
    XTALOSC = 0xF10
    XTALAMPL = 0xF11
    TUNE_F18 = 0xF18
    TUNE_F1C = 0xF1C
    TUNE_F21 = 0xF21
    TUNE_F22 = 0xF22
    TUNE_F23 = 0xF23
    TUNE_F26 = 0xF26
    TUNE_F30 = 0xF30
    TUNE_F31 = 0xF31
    TUNE_F32 = 0xF32
    TUNE_F33 = 0xF33
    TUNE_F34 = 0xF34
    TUNE_F35 = 0xF35
    TUNE_F44 = 0xF44
    MODCFGP = 0xF5F
    TUNE_F72 = 0xF72

@unique
class Pwrmode(IntEnum):
    POWERDOWN = 0x0
    DEEPSLEEP = 0x1
    STANDBY = 0x5
    FIFOON  = 0x7
    SYNTHRX = 0x8
    FULLRX = 0x9
    WORRX = 0xB
    SYNTHTX = 0xC
    FULLTX = 0xD

class Bits(IntEnum):
    # POWSTAT
    SVMODEM = 0x08
    # XTALSTATUS
    XTAL_RUN = 0x01
    # PLLRANGINGA
    RNG_START = 0x10
    RNGERR = 0x20

@unique
class Fifocmd(IntEnum):
    CLEAR_DATA_FLAGS = 0x03
    COMMIT = 0x04

class Chunk:
    def from_bytes(buf):
        chunk_size = Chunk.check_length(buf)
        if not chunk_size: return (None, buf)

        rem = buf[chunk_size:]
        if buf[0] == 0x31:
            return (RssiChunk(buf[1]), rem)
        elif buf[0] == 0x52:
            return (FreqoffsChunk(buf[1], buf[2]), rem)
        elif buf[0] == 0x55:
            return (Antrssi2Chunk(buf[1], buf[2]), rem)
        elif buf[0] == 0x70:
            return (TimerChunk(buf[1], buf[2], buf[3]), rem)
        elif buf[0] == 0x73:
            return (RffreqoffsChunk(buf[1], buf[2], buf[3]), rem)
        elif buf[0] == 0x74:
            return (DatarateChunk(buf[1], buf[2], buf[3]), rem)
        elif buf[0] == 0x75:
            return (Antrssi3Chunk(buf[1], buf[2], buf[3]), rem)
        elif buf[0] == 0xE1:
            length = buf[1]
            return (DataChunk(buf[2], buf[3:chunk_size]), rem)
        else:
            return (UnknownChunk(buf[0:chunk_size]), rem)

    def check_length(buf):
        assert len(buf) > 0
        top = buf[0] & 0xE0
        if top == 0x00: return True
        elif top == 0x20: return 2*(len(buf) >= 2)
        elif top == 0x40: return 3*(len(buf) >= 3)
        elif top == 0x60: return 4*(len(buf) >= 4)
        elif top == 0xE0:
            if len(buf) < 1: return False
            else:
                length = buf[1]
                return (length + 2)*(len(buf) >= length + 2)
        else:
            raise RuntimeError('Invalid top bits: %02X' % top)

    def signed_byte(b):
        if b < 128: return b
        else: return b - 256

class RssiChunk(Chunk):
    def __init__(self, rssi):
        self.rssi = Chunk.signed_byte(rssi)

class FreqoffsChunk(Chunk):
    def __init__(self, freqoffs1, freqoffs0):
        self.freqoffs = (freqoffs1 << 8) | freqoffs0

class Antrssi2Chunk(Chunk):
    def __init__(self, rssi, bgndnoise):
        self.rssi = Chunk.signed_byte(rssi)
        self.bgndnoise = Chunk.signed_byte(bgndnoise)

class TimerChunk(Chunk):
    def __init__(self, timer2, timer1, timer0):
        self.timer = (timer2 << 16) | (timer1 << 8) | timer0

class RffreqoffsChunk(Chunk):
    def __init__(self, rffreqoffs2, rffreqoffs1, rffreqoffs0):
        self.rffreqoffs = (rffreqoffs2 << 16) | (rffreqoffs1 << 8) | rffreqoffs0

class DatarateChunk(Chunk):
    def __init__(self, datarate2, datarate1, datarate0):
        self.datarate = (datarate2 << 16) | (datarate1 << 8) | datarate0

class Antrssi3Chunk(Chunk):
    def __init__(self, antorssi2, antorssi1, antorssi0):
        # Programming manual suggests fields should be ANT0RSSI, ANT1RSSI, and BGNDNOISE
        self.antorssi2 = antorssi2
        self.antorssi1 = antorssi1
        self.antorssi0 = antorssi0

class DataChunk(Chunk):
    def __init__(self, flags, data):
        self.flags = flags
        self.data = data

class UnknownChunk(Chunk):
    def __init__(self, buf):
        self.buf = buf

# Note: CE0 is used as CS pin by Linux system calls (and is NOT held between
# Python calls, even in the same context), so all reads must use write_readinto.
class Ax5043:
    def __init__(self, bus):
        self._bus = bus

    def execute(self, cmds):
        last_addr = -2
        addr_wvals = None
        for addr, value in sorted(cmds.items()):
            if addr - last_addr != 1:
                # Write accumulated contiguous bytes
                if addr_wvals is not None:
                    with self._bus as spi: spi.write(addr_wvals)

                # Initialize next write buffer
                if addr < 0x70:
                    addr_wvals = bytearray([0x80 | addr])
                else:
                    addr_wvals = bytearray([0xF0 | (addr >> 8), addr & 0xFF])

            addr_wvals.append(value)
            last_addr = addr

        # Write accumulated contiguous bytes
        if addr_wvals is not None:
            with self._bus as spi: spi.write(addr_wvals)
        # Enhancements: return status bits?

    def read(self, addr):
        if addr < 0x70:
            addr_wvals = bytearray([addr, 0])
        else:
            addr_wvals = bytearray([0x70 | (addr >> 8), addr & 0xFF, 0])
        rvals = bytearray(len(addr_wvals))
        with self._bus as spi: spi.write_readinto(addr_wvals, rvals)
        return rvals[-1]

    def read_16(self, addr):
        if addr < 0x70:
            addr_wvals = bytearray([addr, 0, 0])
        else:
            addr_wvals = bytearray([0x70 | (addr >> 8), addr & 0xFF, 0, 0])
        rvals = bytearray(len(addr_wvals))
        with self._bus as spi: spi.write_readinto(addr_wvals, rvals)
        return (rvals[-2] << 8) | rvals[-1]

    def set_pwrmode(self, mode):
        # Always sets REFEN, XOEN high
        self.execute({Reg.PWRMODE: 0x50 | mode})

    def reset(self):
        self.execute({Reg.PWRMODE: 0xE0})
        self.execute({Reg.PWRMODE: 0x50})

    def write_fifo(self, values):
        # Writing to FIFODATA does not auto-advance the SPI address pointer
        addr_wvals = bytearray([0x80 | Reg.FIFODATA]) + values
        rvals = bytearray(len(addr_wvals))
        with self._bus as spi: spi.write_readinto(addr_wvals, rvals)
        # TODO: Check FIFO status in rvals

    def write_fifo_data(self, data):
        # TODO: Document flags
        self.write_fifo(bytearray([0xE1, len(data) + 1, 0x13]) + data)

    def read_fifo(self, count):
        addr_wvals = bytearray([Reg.FIFODATA]) + bytearray(count)
        rvals = bytearray(len(addr_wvals))
        with self._bus as spi: spi.write_readinto(addr_wvals, rvals)
        return rvals[1:]
