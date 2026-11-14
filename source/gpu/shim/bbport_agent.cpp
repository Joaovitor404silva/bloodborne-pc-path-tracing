// SPDX-License-Identifier: GPL-2.0-or-later
// AgentLink host (docs/AGENT_HOST.md): publishes the main camera and frame clock for agentd and
// hands the latest agent pad command to the pad code. BB_AGENTLINK=0 turns it off. Without
// agentd nothing is injected: a command older than its ttl is ignored.
#include "agentlink.h"
#include "bbport_toggles.h"
#include "../bbgpu.h"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>

namespace {
std::atomic<bool> g_camera_seen{false};

// Bloodborne 1.09 WorldChrMan (docs/AGENT_HOST.md "Characters"). PS4 VAs (eboot base 0x400000, as in
// patches/Bloodborne.xml) land at 0x800000000 + (va - 0x400000), moved by the image offset BloodborneCam
// found. Each pointer is checked against its class vtable before use.
constexpr uintptr_t kImage = 0x800000000 - 0x400000;
constexpr uintptr_t kWcmGlobal = kImage + 0x593E878, kVtPlayerIns = kImage + 0x578F310, kVtDataModule = kImage + 0x5735810;
constexpr uintptr_t kWcmPlayer = 0x60, kWcmInfo = 0x08, kInfoBlocks = 0x18, kWcmSets = 0x850;
constexpr uintptr_t kChrModules = 0x3B0, kModData = 0x20, kModPhys = 0x68, kChrHandle = 0x08;
constexpr uintptr_t kDataHp = 0xF8, kDataHpMax = 0xFC, kDataSta = 0x134, kPhysPos = 0x1E0;
constexpr uint32_t kMaxSets = 0x3E, kEntryStride = 0x38, kMaxSetCap = 4096;

struct Chr { float hp, hp_max, pos[3]; };
struct World {
    bool player = false; Chr me{}; float stamina = 0;
    uint32_t n = 0; AglEntity e[AGL_MAX_ENTITIES]{};
};
World g_world;

template <class T> inline T Rd(uintptr_t a) { return *reinterpret_cast<const volatile T*>(a); }
inline bool Ptr(uintptr_t p) { return p >= 0x10000 && !(p & 7) && p < (1ull << 47); }

// Reads may fault (a character freed mid-read): the caller holds a recovery point.
bool ReadChr(uintptr_t chr, intptr_t off, Chr& c, uintptr_t* data_out = nullptr) {
    const uintptr_t m = Rd<uintptr_t>(chr + kChrModules);
    if (!Ptr(m)) return false;
    const uintptr_t d = Rd<uintptr_t>(m + kModData), t = Rd<uintptr_t>(m + kModPhys);
    if (!Ptr(d) || !Ptr(t) || Rd<uintptr_t>(d) != kVtDataModule + off) return false;
    c.hp = float(Rd<int32_t>(d + kDataHp));
    c.hp_max = float(Rd<int32_t>(d + kDataHpMax));
    for (int i = 0; i < 3; ++i) c.pos[i] = Rd<float>(t + kPhysPos + 4 * i);
    if (data_out) *data_out = d;
    return c.hp_max > 0 && c.hp_max < 1e6f && std::isfinite(c.pos[0]) && std::isfinite(c.pos[1]) &&
           std::isfinite(c.pos[2]) && std::fabs(c.pos[0]) < 1e5f && std::fabs(c.pos[1]) < 1e5f && std::fabs(c.pos[2]) < 1e5f;
}

void ReadWorldUnsafe(intptr_t off, bool scan, World& w) {
    w.player = false;
    const uintptr_t wcm = Rd<uintptr_t>(kWcmGlobal + off);
    if (!Ptr(wcm)) return;
    const uintptr_t me = Rd<uintptr_t>(wcm + kWcmPlayer);
    uintptr_t data = 0;
    if (!Ptr(me) || Rd<uintptr_t>(me) != kVtPlayerIns + off || !ReadChr(me, off, w.me, &data)) return; // title, loads
    w.stamina = float(Rd<int32_t>(data + kDataSta));
    w.player = true;
    if (!scan) return;
    // Loaded characters: handle_chr_sets[selector] -> {u32 capacity, entries}, entry stride 0x38, ChrIns* at +0.
    struct Near { float d2; AglEntity e; };
    static Near found[512];
    uint32_t nf = 0;
    const uintptr_t info = Rd<uintptr_t>(wcm + kWcmInfo);
    const uint32_t sets = Ptr(info) ? std::min<uint32_t>(Rd<uint32_t>(info + kInfoBlocks) + 2, kMaxSets) : 2;
    for (uint32_t s = 0; s < sets; ++s) {
        const uintptr_t set = Rd<uintptr_t>(wcm + kWcmSets + 8 * s);
        if (!Ptr(set)) continue;
        const uint32_t cap = Rd<uint32_t>(set);
        const uintptr_t entries = Rd<uintptr_t>(set + 8);
        if (!Ptr(entries) || cap > kMaxSetCap) continue;
        for (uint32_t i = 0; i < cap && nf < std::size(found); ++i) {
            const uintptr_t chr = Rd<uintptr_t>(entries + uintptr_t(i) * kEntryStride);
            Chr c;
            uintptr_t d = 0;
            if (!Ptr(chr) || chr == me || !ReadChr(chr, off, c, &d) || c.hp < 1) continue; // empty, player, dead
            Near& n = found[nf++];
            n.e = AglEntity{};
            n.e.id = Rd<uint32_t>(chr + kChrHandle);
            n.e.kind = 1;
            std::memcpy(n.e.pos, c.pos, sizeof(c.pos));
            n.e.hp_pct = 100.0f * c.hp / c.hp_max;
            std::snprintf(n.e.name, sizeof(n.e.name), "hp %d", int(c.hp_max)); // no name field known yet
            float d2 = 0;
            for (int k = 0; k < 3; ++k) d2 += (c.pos[k] - w.me.pos[k]) * (c.pos[k] - w.me.pos[k]);
            n.d2 = d2;
        }
    }
    const uint32_t keep = std::min<uint32_t>(nf, AGL_MAX_ENTITIES);
    std::partial_sort(found, found + keep, found + nf, [](const Near& a, const Near& b) { return a.d2 < b.d2; });
    for (uint32_t i = 0; i < keep; ++i) w.e[i] = found[i].e;
    w.n = keep;
}

// One read of the player (+ the character table when `scan`), safe against faults.
bool ReadWorld(intptr_t off, bool scan, World& w) {
    sigjmp_buf recover;
    if (sigsetjmp(recover, 0)) { // a pointer went stale mid-read: the handler cleared the recovery point
        w.player = false;
        return false;
    }
    runtime_fault_recover = &recover;
    ReadWorldUnsafe(off, scan, w);
    runtime_fault_recover = nullptr;
    return true;
}

AglLink* Link() {
    static AglLink* link = [] {
        const char* env = std::getenv("BB_AGENTLINK");
        if (env && !std::strcmp(env, "0")) return static_cast<AglLink*>(nullptr);
        AglLink* l = agl_open(GetCurrentProcessId(), 1);
        if (!l) {
            std::printf("AgentLink: shared memory failed\n");
            return l;
        }
        l->h.host_kind = AGL_HOST_PAD;
        l->h.up_axis = 1;
        l->h.caps = AGL_CAP_STICKS;
        std::snprintf(l->h.game, sizeof(l->h.game), "bloodborne");
        std::printf("AgentLink: Local\\AgentLink_%lu ready\n", GetCurrentProcessId());
        return l;
    }();
    return link;
}
} // namespace

extern "C" void bbgpu_agent_camera(const float* view, const float* inv_view, const float* proj,
                                   uint32_t render_w, uint32_t render_h) {
    AglLink* l = Link();
    if (!l) return;
    static uint64_t frame = 0;
    static double last_ms = 0;
    const double now = agl_now_ms();
    ++frame;
    agl_begin(&l->frame.seq);
    l->frame.frame_id = frame;
    l->frame.host_ms = now;
    l->frame.dt_ms = last_ms ? float(now - last_ms) : 0.0f;
    agl_end(&l->frame.seq);
    last_ms = now;

    // View space looks down +z (clip w = z): forward is the inverse view's third column.
    const float pos[3] = {inv_view[3], inv_view[7], inv_view[11]};
    float fwd[3] = {inv_view[2], inv_view[6], inv_view[10]};
    const float len = std::sqrt(fwd[0] * fwd[0] + fwd[1] * fwd[1] + fwd[2] * fwd[2]);
    if (len > 0) for (float& v : fwd) v /= len;
    agl_begin(&l->camera.seq);
    l->camera.valid = 1;
    l->camera.frame_id = frame;
    std::memcpy(l->camera.pos, pos, sizeof(pos));
    std::memcpy(l->camera.fwd, fwd, sizeof(fwd));
    std::memcpy(l->camera.view, view, 12 * sizeof(float));
    std::memcpy(l->camera.inv_view, inv_view, 12 * sizeof(float));
    std::memcpy(l->camera.proj, proj, 4 * sizeof(float));
    l->camera.render_w = render_w;
    l->camera.render_h = render_h;
    agl_end(&l->camera.seq);
    g_camera_seen = true;
}

// The game's thread, from the camera hook (bloodborne_cam.cpp): the camera orbits a pivot that
// follows the player (+0xD0), is drawn from +0x100, and +0x154 is 1.0 while locked on. Position,
// hp and stamina come from the player character (WorldChrMan) when it reads back valid; the pivot
// stands in for the position (AGL_V_PROXY) otherwise. Characters are read 10 times a second.
extern "C" void bbgpu_agent_pivot(uintptr_t camera, intptr_t image_offset) {
    AglLink* l = Link();
    if (!l || !camera) return;
    const volatile float* c = reinterpret_cast<const volatile float*>(camera);
    float pos[3] = {c[0xD0 / 4], c[0xD4 / 4], c[0xD8 / 4]};
    if (!std::isfinite(pos[0]) || !std::isfinite(pos[1]) || !std::isfinite(pos[2])) return;
    const bool locked = c[0x154 / 4] == 1.0f;
    static float last[3];
    static double last_ms, scan_ms;
    const double now = agl_now_ms();
    const bool scan = now - scan_ms >= 100;
    if (scan) scan_ms = now;
    ReadWorld(image_offset, scan, g_world);
    const World& w = g_world;
    // The character position must agree with the pivot (a few metres): else the read is not trusted.
    float d2 = 0;
    for (int i = 0; i < 3; ++i) d2 += (w.me.pos[i] - pos[i]) * (w.me.pos[i] - pos[i]);
    const bool real = w.player && d2 < 25.0f;
    if (real) std::memcpy(pos, w.me.pos, sizeof(pos));
    const float dt = last_ms ? float((now - last_ms) / 1000.0) : 0.0f;
    agl_begin(&l->player.seq);
    l->player.valid = AGL_V_POS | AGL_V_FLAGS | (dt > 0 ? AGL_V_VEL : 0u) |
                      (real ? AGL_V_HP | AGL_V_STAMINA : AGL_V_PROXY);
    l->player.frame_id++;
    std::memcpy(l->player.pos, pos, sizeof(pos));
    for (int i = 0; i < 3; ++i) l->player.vel[i] = dt > 0 ? (pos[i] - last[i]) / dt : 0.0f;
    if (real) {
        l->player.hp = w.me.hp;
        l->player.hp_max = w.me.hp_max;
        l->player.stamina = w.stamina;
    }
    l->player.flags = (!real || w.me.hp >= 1 ? AGL_F_ALIVE : 0u) | (locked ? AGL_F_LOCKED_ON : 0u);
    agl_end(&l->player.seq);
    if (scan) {
        agl_begin(&l->ents.seq);
        l->ents.frame_id++;
        l->ents.count = real ? w.n : 0;
        if (real) std::memcpy(l->ents.e, w.e, w.n * sizeof(AglEntity));
        agl_end(&l->ents.seq);
    }
    std::memcpy(last, pos, sizeof(pos));
    last_ms = now;
}

// Window thread: hook the camera update for the pivot once the game draws a camera.
extern "C" int bbgpu_agent_wants_camera_hook(void) {
    return Link() && g_camera_seen;
}

extern "C" int bbgpu_agent_command(uint32_t* buttons, float stick[4]) {
    AglLink* l = Link();
    if (!l) return 0;
    l->h.reserved[0]++; // pad reads (pad thread is the only writer)
    AglCommand c;
    if (!agl_read(&l->cmd, sizeof(c), &c) || !c.issued_ms) return 0;
    if (agl_now_ms() - c.issued_ms > c.ttl_ms) return 0;
    l->h.reserved[1] = c.cmd_seq; // last applied command
    *buttons = c.buttons;
    std::memcpy(stick, c.stick, 4 * sizeof(float));
    return 1;
}
