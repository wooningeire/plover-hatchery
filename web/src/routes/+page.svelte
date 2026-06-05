<script lang="ts">
type CompileDictionaryResult = {
    path?: string;
    status?: string;
    [key: string]: unknown;
};

type CompileResponse = {
    dictionaries: CompileDictionaryResult[];
    error?: string;
};

type CompileState = "idle" | "compiling" | "compiled" | "error";
type CompileAction = "compile" | "refresh";

let compileState = $state<CompileState>("idle");
let compileAction = $state<CompileAction>("compile");
let compileResult = $state<CompileResponse | null>(null);
let compileError = $state<string | null>(null);

const compiledDictionaryCount = $derived(compileResult?.dictionaries.length ?? 0);
const compileIsWorking = $derived(compileState === "compiling");

function apiBaseUrl() {
    if (typeof window === "undefined") {
        return "http://localhost:5325";
    }

    const host = window.location.hostname === "127.0.0.1"
        ? "127.0.0.1"
        : "localhost";

    return `http://${host}:5325`;
}

async function parseJsonResponse(response: Response) {
    try {
        return await response.json();
    } catch {
        return null;
    }
}

function dictionaryLabel(dictionary: CompileDictionaryResult) {
    if (typeof dictionary.path === "string" && dictionary.path !== "") {
        return dictionary.path;
    }

    return "Hatchery dictionary";
}

function dictionaryStatus(dictionary: CompileDictionaryResult) {
    if (typeof dictionary.status === "string" && dictionary.status !== "") {
        return dictionary.status.replaceAll("_", " ");
    }

    return "compiled";
}

async function compileTheory(refreshCache = false) {
    compileState = "compiling";
    compileAction = refreshCache ? "refresh" : "compile";
    compileResult = null;
    compileError = null;

    try {
        const response = await fetch(`${apiBaseUrl()}/api/compile`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ refreshCache }),
        });
        const responseBody = await parseJsonResponse(response) as CompileResponse | null;

        if (!response.ok) {
            throw new Error(responseBody?.error ?? `Compile failed with HTTP ${response.status}`);
        }

        compileResult = responseBody ?? { dictionaries: [] };
        compileState = "compiled";
    } catch (error) {
        compileState = "error";
        compileError = error instanceof Error ? error.message : String(error);
    }
}
</script>

<main class="page">
    <header class="topbar">
        <div>
            <p class="eyebrow">Hatchery</p>
            <h1>Theory compiler</h1>
        </div>

        <div class="actions">
            <button
                class="compile-button"
                class:is-working={compileIsWorking && compileAction === "compile"}
                disabled={compileIsWorking}
                onclick={() => compileTheory(false)}
            >
                {compileIsWorking && compileAction === "compile" ? "Compiling..." : "Compile theory"}
            </button>

            <button
                class="compile-button secondary"
                class:is-working={compileIsWorking && compileAction === "refresh"}
                disabled={compileIsWorking}
                onclick={() => compileTheory(true)}
            >
                {compileIsWorking && compileAction === "refresh" ? "Refreshing..." : "Refresh cache"}
            </button>
        </div>
    </header>

    <section
        class="status-strip"
        class:is-success={compileState === "compiled"}
        class:is-error={compileState === "error"}
        aria-live="polite"
    >
        {#if compileState === "idle"}
            <span class="status-dot"></span>
            <span>Ready</span>
        {:else if compileState === "compiling"}
            <span class="spinner"></span>
            <span>{compileAction === "refresh" ? "Refreshing cache" : "Compiling theory"}</span>
        {:else if compileState === "compiled"}
            <span class="status-dot"></span>
            <span>Compiled {compiledDictionaryCount} {compiledDictionaryCount === 1 ? "dictionary" : "dictionaries"}</span>
        {:else}
            <span class="status-dot"></span>
            <span>{compileError ?? "Compile failed"}</span>
        {/if}
    </section>

    {#if compileResult !== null && compileResult.dictionaries.length > 0}
        <section class="dictionary-results" aria-label="Dictionary compile results">
            {#each compileResult.dictionaries as dictionary}
                <article class="dictionary-result">
                    <span class="dictionary-path">{dictionaryLabel(dictionary)}</span>
                    <span class="dictionary-status">{dictionaryStatus(dictionary)}</span>
                </article>
            {/each}
        </section>
    {/if}
</main>

<style lang="scss">
.page {
    min-height: 100vh;
    background: #f7f8f5;
    color: #17211b;
}

.topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;

    padding: 1rem clamp(1rem, 3vw, 2rem);
    border-bottom: 1px solid #d7ddd1;
    background: #ffffff;
}

.eyebrow {
    margin: 0 0 0.15rem;
    color: #526257;
    font-size: 0.78rem;
    font-weight: 700;
    text-transform: uppercase;
}

h1 {
    margin: 0;
    font-size: clamp(1.25rem, 2vw, 1.75rem);
    font-weight: 750;
}

.actions {
    display: flex;
    gap: 0.5rem;
}

.compile-button {
    min-width: 9.75rem;
    min-height: 2.5rem;
    padding: 0 1rem;

    border: 1px solid #1f6f51;
    border-radius: 4px;
    background: #24825f;
    color: #fff;
    cursor: pointer;
    font-weight: 750;
}

.compile-button:hover:not(:disabled) {
    background: #1f6f51;
}

.compile-button.secondary {
    border-color: #9aa69d;
    background: #ffffff;
    color: #28342c;
}

.compile-button.secondary:hover:not(:disabled) {
    background: #eef1ea;
}

.compile-button:disabled {
    cursor: wait;
    opacity: 0.74;
}

.status-strip {
    display: flex;
    align-items: center;
    gap: 0.5rem;

    min-height: 2.75rem;
    padding: 0.65rem clamp(1rem, 3vw, 2rem);
    border-bottom: 1px solid #d7ddd1;
    background: #eef1ea;
    color: #475249;
    font-size: 0.95rem;
}

.status-strip.is-success {
    background: #e7f5ec;
    color: #195e3d;
}

.status-strip.is-error {
    background: #fff0ed;
    color: #9c2b1d;
}

.status-dot,
.spinner {
    width: 0.65rem;
    height: 0.65rem;
    flex: 0 0 auto;
    border-radius: 50%;
    background: currentColor;
}

.spinner {
    border: 2px solid currentColor;
    border-right-color: transparent;
    background: transparent;
    animation: spin 0.72s linear infinite;
}

.dictionary-results {
    display: grid;
    gap: 0.5rem;

    padding: 1rem clamp(1rem, 3vw, 2rem);
    border-bottom: 1px solid #d7ddd1;
    background: #ffffff;
}

.dictionary-result {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    align-items: center;
    gap: 1rem;

    min-height: 2.25rem;
    padding: 0.5rem 0.75rem;
    border: 1px solid #dfe4dc;
    border-radius: 4px;
}

.dictionary-path {
    min-width: 0;
    overflow: hidden;
    color: #28342c;
    font-family: "Atkinson Hyperlegible Mono", monospace;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.dictionary-status {
    color: #526257;
    font-size: 0.88rem;
    font-weight: 700;
    text-transform: capitalize;
}

@keyframes spin {
    to {
        transform: rotate(1turn);
    }
}

@media (max-width: 560px) {
    .topbar {
        align-items: stretch;
        flex-direction: column;
    }

    .compile-button {
        width: 100%;
    }

    .actions {
        flex-direction: column;
    }

    .dictionary-result {
        grid-template-columns: 1fr;
        gap: 0.25rem;
    }
}
</style>
