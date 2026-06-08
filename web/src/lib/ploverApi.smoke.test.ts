/**
 * n.b. this is not an automated test script; test with Plover's Hatchery web extension on and off
 */

import {
    PloverApiError,
    deletePloverEntry,
    loadLookupBreakdown,
    loadPloverDictionaryEntries,
    loadPloverDictionaries,
} from "./ploverApi.js";

type FetchImplementation = typeof fetch;


const originalFetch = globalThis.fetch;

function assert(condition: unknown, message: string): asserts condition {
    if (!condition) {
        throw new Error(message);
    }
}

const withFetch = async (
    fetchImplementation: FetchImplementation,
    callback: () => Promise<void>,
) => {
    globalThis.fetch = fetchImplementation;

    try {
        await callback();
    } finally {
        globalThis.fetch = originalFetch;
    }
};

const jsonResponse = (value: unknown, init?: ResponseInit) => (
    new Response(JSON.stringify(value), {
        status: 200,
        ...init,
        headers: {
            "Content-Type": "application/json",
            ...init?.headers,
        },
    })
);

const assertRejectsWithPloverApiError = async (
    callback: () => Promise<unknown>,
    expectedKind: PloverApiError["kind"],
    expectedMessageText: string,
) => {
    try {
        await callback();
    } catch (error) {
        assert(error instanceof PloverApiError, "Expected a PloverApiError");
        assert(error.kind === expectedKind, `Expected ${expectedKind}, got ${error.kind}`);
        assert(
            error.message.includes(expectedMessageText),
            `Expected message to include "${expectedMessageText}", got "${error.message}"`,
        );
        return;
    }

    throw new Error("Expected promise to reject");
};

const test = async (name: string, callback: () => Promise<void>) => {
    await callback();
    console.log(`ok - ${name}`);
};


await test("loadPloverDictionaries reports when local Plover is unreachable", async () => {
    await withFetch(
        () => Promise.reject(new TypeError("fetch failed")),
        async () => {
            await assertRejectsWithPloverApiError(
                () => loadPloverDictionaries(),
                "connection",
                "Could not reach the Hatchery API",
            );
        },
    );
});

await test("loadPloverDictionaries reports when another service uses the Plover port", async () => {
    await withFetch(
        () => Promise.resolve(jsonResponse({
            ok: true,
        })),
        async () => {
            await assertRejectsWithPloverApiError(
                () => loadPloverDictionaries(),
                "wrong-server",
                "it is not the Hatchery API",
            );
        },
    );
});

await test("loadPloverDictionaries accepts Hatchery status before reading dictionaries", async () => {
    const requestedPaths: string[] = [];

    await withFetch(
        (input) => {
            const url = String(input);
            requestedPaths.push(new URL(url).pathname);

            if (url.endsWith("/api/status")) {
                return Promise.resolve(jsonResponse({
                    service: "plover-hatchery",
                    ok: true,
                }));
            }

            return Promise.resolve(jsonResponse({
                dictionaries: [
                    {
                        path: "user.hatchery",
                        label: "user.hatchery",
                    },
                ],
            }));
        },
        async () => {
            const response = await loadPloverDictionaries();

            assert(requestedPaths.join(",") === "/api/status,/api/dictionaries", "Expected status check before dictionaries request");
            assert(response.dictionaries.length === 1, "Expected one dictionary");
            assert(response.dictionaries[0]?.path === "user.hatchery", "Expected dictionary path");
        },
    );
});

await test("loadPloverDictionaryEntries reads selected dictionary entries", async () => {
    await withFetch(
        (input) => {
            const url = new URL(String(input));

            assert(url.pathname === "/api/entries", "Expected entries path");
            assert(url.searchParams.get("dictionaryPath") === "user.hatchery", "Expected dictionary path query");
            assert(url.searchParams.get("offset") === "25", "Expected offset query");
            assert(url.searchParams.get("limit") === "50", "Expected limit query");
            assert(url.searchParams.get("query") === "cat", "Expected filter query");

            return Promise.resolve(jsonResponse({
                dictionary: {
                    path: "user.hatchery",
                    label: "user.hatchery",
                },
                stats: {
                    morphemeCount: 1,
                    entryCount: 1,
                    definitionCount: 2,
                },
                entries: [
                    {
                        key: "cat",
                        translation: "cat",
                        definition: "{@k} a.a t.t",
                    },
                ],
                pagination: {
                    offset: 25,
                    limit: 50,
                    totalCount: 90,
                    returnedCount: 1,
                    hasPrevious: true,
                    hasNext: true,
                    query: "cat",
                },
            }));
        },
        async () => {
            const response = await loadPloverDictionaryEntries("user.hatchery", {
                offset: 25,
                limit: 50,
                query: "cat",
            });

            assert(response.stats.entryCount === 1, "Expected one entry");
            assert(response.entries[0]?.key === "cat", "Expected entry key");
            assert(response.pagination.totalCount === 90, "Expected pagination count");
        },
    );
});

await test("loadLookupBreakdown checks Hatchery identity before reading lookup data", async () => {
    const requestedPaths: string[] = [];

    await withFetch(
        (input) => {
            const url = new URL(String(input));
            requestedPaths.push(url.pathname);

            if (url.pathname === "/api/status") {
                return Promise.resolve(jsonResponse({
                    service: "plover-hatchery",
                    ok: true,
                }));
            }

            assert(url.pathname === "/api/breakdown_lookup/APL%20%5ETPEU", "Expected lookup path");
            return Promise.resolve(jsonResponse([
                {
                    path: [
                        {
                            chord: "A",
                            nodes: [0, 1],
                            theory_symbols: ["A"],
                        },
                    ],
                },
            ]));
        },
        async () => {
            const response = await loadLookupBreakdown("APL/^TPEU");

            assert(requestedPaths.join(",") === "/api/status,/api/breakdown_lookup/APL%20%5ETPEU", "Expected status check before lookup request");
            assert(response.length === 1, "Expected one lookup breakdown");
        },
    );
});

await test("loadLookupBreakdown reports Hatchery JSON endpoint errors as HTTP errors", async () => {
    await withFetch(
        (input) => {
            const url = new URL(String(input));

            if (url.pathname === "/api/status") {
                return Promise.resolve(jsonResponse({
                    service: "plover-hatchery",
                    ok: true,
                }));
            }

            return Promise.resolve(jsonResponse({
                error: "Lookup failed",
            }, {
                status: 500,
            }));
        },
        async () => {
            await assertRejectsWithPloverApiError(
                () => loadLookupBreakdown("APL/^TPEU"),
                "http",
                "Lookup failed",
            );
        },
    );
});

await test("loadLookupBreakdown reports non-JSON Hatchery endpoint failures as HTTP errors", async () => {
    await withFetch(
        (input) => {
            const url = new URL(String(input));

            if (url.pathname === "/api/status") {
                return Promise.resolve(jsonResponse({
                    service: "plover-hatchery",
                    ok: true,
                }));
            }

            return Promise.resolve(new Response("<!doctype html>Internal Server Error", {
                status: 500,
                headers: {
                    "Content-Type": "text/html",
                },
            }));
        },
        async () => {
            await assertRejectsWithPloverApiError(
                () => loadLookupBreakdown("APL/^TPEU"),
                "http",
                "did not return JSON",
            );
        },
    );
});

await test("deletePloverEntry deletes selected dictionary entry", async () => {
    await withFetch(
        (_input, init) => {
            assert(init?.method === "DELETE", "Expected DELETE request");
            assert(typeof init.body === "string", "Expected JSON body");

            const requestBody = JSON.parse(init.body);
            assert(requestBody.dictionaryPath === "user.hatchery", "Expected dictionary path body");
            assert(requestBody.entryKey === "cat", "Expected entry key body");

            return Promise.resolve(jsonResponse({
                entry: {
                    key: "cat",
                    translation: "cat",
                    definition: "{@k} a.a t.t",
                },
                compile: {
                    path: "user.hatchery",
                    status: "compiled",
                },
            }));
        },
        async () => {
            const response = await deletePloverEntry("user.hatchery", "cat");

            assert(response.entry.key === "cat", "Expected deleted entry key");
            assert(response.compile.status === "compiled", "Expected compile result");
        },
    );
});
