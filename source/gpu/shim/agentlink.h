// AgentLink v1: shared memory between a game host and agentd (docs/agent/*-design.md).
// C and C++. One writer thread per block; every block starts with a seqlock word (odd while writing).
// Coordinates are the host's world units (metres) and axes; header.up_axis says which axis is up.
#pragma once
#include <stdint.h>
#include <string.h>

#define AGL_MAGIC 0x314C4741u /* "AGL1" */
#define AGL_VERSION 1u
#define AGL_SIZE 65536u
#define AGL_MAX_ENTITIES 64

enum { AGL_HOST_SIM = 1, AGL_HOST_UE = 2, AGL_HOST_PAD = 3 };
/* header.caps */
enum {
    AGL_CAP_STICKS = 1u << 0,     /* host applies cmd.stick[] / cmd.buttons as a gamepad */
    AGL_CAP_WORLD_MOVE = 1u << 1, /* host applies cmd.move[] as a world direction */
    AGL_CAP_LOOK = 1u << 2,       /* host applies cmd.look[] (target yaw/pitch) */
    AGL_CAP_TELEPORT = 1u << 3,
    AGL_CAP_KEYS = 1u << 4        /* buttons are mapped to keys by the host */
};
/* player.valid / camera.valid bits */
enum {
    AGL_V_POS = 1u << 0, AGL_V_VEL = 1u << 1, AGL_V_YAW = 1u << 2, AGL_V_HP = 1u << 3,
    AGL_V_STAMINA = 1u << 4, AGL_V_AREA = 1u << 5, AGL_V_FLAGS = 1u << 6,
    AGL_V_PROXY = 1u << 7         /* pos is derived (e.g. camera + offset), not the real player */
};
/* player.flags */
enum {
    AGL_F_ALIVE = 1u << 0, AGL_F_MENU = 1u << 1, AGL_F_DIALOG = 1u << 2, AGL_F_LOADING = 1u << 3,
    AGL_F_GROUNDED = 1u << 4, AGL_F_LOCKED_ON = 1u << 5
};
/* pad buttons (DualShock layout; key hosts map them by profile) */
enum {
    AGL_B_CROSS = 1u << 0, AGL_B_CIRCLE = 1u << 1, AGL_B_SQUARE = 1u << 2, AGL_B_TRIANGLE = 1u << 3,
    AGL_B_L1 = 1u << 4, AGL_B_R1 = 1u << 5, AGL_B_L2 = 1u << 6, AGL_B_R2 = 1u << 7,
    AGL_B_L3 = 1u << 8, AGL_B_R3 = 1u << 9, AGL_B_OPTIONS = 1u << 10, AGL_B_TOUCHPAD = 1u << 11,
    AGL_B_UP = 1u << 12, AGL_B_DOWN = 1u << 13, AGL_B_LEFT = 1u << 14, AGL_B_RIGHT = 1u << 15
};

typedef struct AglHeader {
    uint32_t magic, version, size, host_kind;
    uint32_t pid, up_axis, caps, reserved0;
    char game[32];
    uint32_t reserved[8];
} AglHeader;

typedef struct AglFrame {
    volatile uint32_t seq; uint32_t pad0;
    uint64_t frame_id;
    double host_ms;   /* agl_now_ms() when published */
    float dt_ms; float pad1;
} AglFrame;

typedef struct AglPlayer {
    volatile uint32_t seq; uint32_t valid;
    uint64_t frame_id;
    float pos[3], vel[3];
    float yaw, pitch;   /* degrees */
    float hp, hp_max, stamina;
    uint32_t flags, area_id;
    char area[32];
} AglPlayer;

typedef struct AglCamera {
    volatile uint32_t seq; uint32_t valid; /* 1 = camera fields below are current */
    uint64_t frame_id;
    float pos[3], fwd[3];
    float view[12];     /* world -> view, 3x4 rows */
    float inv_view[12]; /* view -> world, 3x4 rows */
    float proj[4];      /* x scale, y scale, z scale, z offset */
    uint32_t render_w, render_h;
} AglCamera;

typedef struct AglEntity {
    uint32_t id, kind; /* kind: 1 enemy, 2 npc, 3 item, 4 interactable */
    float pos[3]; float hp_pct;
    char name[24];
} AglEntity;

typedef struct AglEntities {
    volatile uint32_t seq; uint32_t count;
    uint64_t frame_id;
    AglEntity e[AGL_MAX_ENTITIES];
} AglEntities;

typedef struct AglCommand {
    volatile uint32_t seq; uint32_t cmd_seq;
    double issued_ms;   /* agl_now_ms() of the writer; host drops input when now - issued_ms > ttl_ms */
    uint32_t ttl_ms, buttons;
    float stick[4];     /* lx, ly, rx, ry in -1..1 (ly -1 = forward, like the pad's up) */
    float move[3];      /* world direction * magnitude 0..1 (AGL_CAP_WORLD_MOVE) */
    float look[2];      /* target yaw, pitch degrees (AGL_CAP_LOOK) */
    float triggers[2];
    float teleport[3];
    uint32_t flags;     /* 1 = teleport pending, 2 = look valid */
    uint32_t pad0;
} AglCommand;

typedef struct AglLink {
    AglHeader h;
    AglFrame frame;
    AglPlayer player;
    AglCamera camera;
    AglCommand cmd;
    AglEntities ents;
} AglLink;

#ifdef __cplusplus
static_assert(sizeof(AglLink) <= AGL_SIZE, "AgentLink too big");
#include <atomic>
#define AGL_FENCE() std::atomic_thread_fence(std::memory_order_seq_cst)
#define AGL_INLINE inline
#else
_Static_assert(sizeof(AglLink) <= AGL_SIZE, "AgentLink too big");
#define AGL_FENCE() __atomic_thread_fence(__ATOMIC_SEQ_CST)
#define AGL_INLINE static inline
#endif

/* Writer side: agl_begin(&blk.seq); fill fields; agl_end(&blk.seq). One writer thread per block. */
AGL_INLINE void agl_begin(volatile uint32_t* seq) { *seq = *seq + 1; AGL_FENCE(); }
AGL_INLINE void agl_end(volatile uint32_t* seq) { AGL_FENCE(); *seq = *seq + 1; }

/* Reader side: copies a whole block (first field = seq) without tearing. 0 = gave up (writer stuck). */
AGL_INLINE int agl_read(const void* block, size_t size, void* out) {
    const volatile uint32_t* seq = (const volatile uint32_t*)block;
    for (int i = 0; i < 1000; ++i) {
        uint32_t a = *seq;
        if (a & 1u) continue;
        AGL_FENCE();
        memcpy(out, (const void*)block, size);
        AGL_FENCE();
        if (*seq == a) return 1;
    }
    return 0;
}

#ifdef _WIN32
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <windows.h>
#include <stdio.h>
AGL_INLINE double agl_now_ms(void) {
    LARGE_INTEGER f, c; QueryPerformanceFrequency(&f); QueryPerformanceCounter(&c);
    return (double)c.QuadPart * 1000.0 / (double)f.QuadPart;
}
/* Host: create = 1 (fills the header). agentd: create = 0. Returns NULL on failure. */
AGL_INLINE AglLink* agl_open(uint32_t pid, int create) {
    wchar_t name[64]; swprintf(name, 64, L"Local\\AgentLink_%u", pid);
    HANDLE m = create ? CreateFileMappingW(INVALID_HANDLE_VALUE, NULL, PAGE_READWRITE, 0, AGL_SIZE, name)
                      : OpenFileMappingW(FILE_MAP_ALL_ACCESS, FALSE, name);
    if (!m) return NULL;
    AglLink* l = (AglLink*)MapViewOfFile(m, FILE_MAP_ALL_ACCESS, 0, 0, AGL_SIZE);
    if (!l) { CloseHandle(m); return NULL; }
    if (create && l->h.magic != AGL_MAGIC) {
        memset(l, 0, sizeof(*l));
        l->h.version = AGL_VERSION; l->h.size = AGL_SIZE; l->h.pid = pid;
        AGL_FENCE();
        l->h.magic = AGL_MAGIC;
    }
    if (!create && (l->h.magic != AGL_MAGIC || l->h.version != AGL_VERSION)) { UnmapViewOfFile(l); CloseHandle(m); return NULL; }
    return l; /* the mapping handle stays open for the process lifetime */
}
#endif
