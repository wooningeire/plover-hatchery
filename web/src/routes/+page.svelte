<script lang="ts">
import { onMount } from "svelte";

type CompileDictionaryResult = {
    path?: string;
    status?: string;
    [key: string]: unknown;
};

type CompileResponse = {
    dictionaries: CompileDictionaryResult[];
    error?: string;
};

type DictionarySummary = {
    path: string;
    label: string;
};

type DictionariesResponse = {
    dictionaries: DictionarySummary[];
    error?: string;
};

type SaveEntryResponse = {
    entry: {
        key: string;
        translation: string;
        definition: string;
    };
    compile: CompileDictionaryResult;
    error?: string;
};

type CompileState = "idle" | "compiling" | "compiled" | "error";
type CompileAction = "compile" | "refresh";
type DictionaryLoadState = "loading" | "loaded" | "error";
type SaveState = "idle" | "saving" | "saved" | "error";

let compileState = $state<CompileState>("idle");
let compileAction = $state<CompileAction>("compile");
let compileResult = $state<CompileResponse | null>(null);
let compileError = $state<string | null>(null);

let dictionaryLoadState = $state<DictionaryLoadState>("loading");
let dictionaryLoadError = $state<string | null>(null);
let dictionaries = $state<DictionarySummary[]>([]);
let selectedDictionaryPath = $state("");

let entryTranslation = $state("");
let entryDefinition = $state("");
let saveState = $state<SaveState>("idle");
let saveError = $state<string | null>(null);
let saveResult = $state<SaveEntryResponse | null>(null);

const compiledDictionaryCount = $derived(compileResult?.dictionaries.length ?? 0);
const compileIsWorking = $derived(compileState === "compiling");
const saveIsWorking = $derived(saveState === "saving");
const selectedDictionary = $derived(
    dictionaries.find((dictionary) => dictionary.path === selectedDictionaryPath) ?? null,
);
const canSaveEntry = $derived(
    !saveIsWorking
    && dictionaryLoadState === "loaded"
    && selectedDictionaryPath !== ""
    && entryTranslation.trim() !== ""
    && entryDefinition.trim() !== "",
);

onMount(() => {
    void loadDictionaries();
});

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

function dictionaryLabel(dictionary: CompileDictionaryResult | DictionarySummary) {
    if ("label" in dictionary && typeof dictionary.label === "string" && dictionary.label !== "") {
        return dictionary.label;
    }

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

function breakdownHref(translation: string) {
    return `/translation/${encodeURIComponent(translation)}`;
}

async function loadDictionaries() {
    dictionaryLoadState = "loading";
    dictionaryLoadError = null;

    try {
        const response = await fetch(`${apiBaseUrl()}/api/dictionaries`);
        const responseBody = await parseJsonResponse(response) as DictionariesResponse | null;

        if (!response.ok) {
            throw new Error(responseBody?.error ?? `Dictionary load failed with HTTP ${response.status}`);
        }

        dictionaries = responseBody?.dictionaries ?? [];
        if (!dictionaries.some((dictionary) => dictionary.path === selectedDictionaryPath)) {
            selectedDictionaryPath = dictionaries[0]?.path ?? "";
        }
        dictionaryLoadState = "loaded";
    } catch (error) {
        dictionaries = [];
        selectedDictionaryPath = "";
        dictionaryLoadState = "error";
        dictionaryLoadError = error instanceof Error ? error.message : String(error);
    }
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

async function saveEntry() {
    if (!canSaveEntry) {
        return;
    }

    saveState = "saving";
    saveResult = null;
    saveError = null;

    try {
        const response = await fetch(`${apiBaseUrl()}/api/entries`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                dictionaryPath: selectedDictionaryPath,
                translation: entryTranslation,
                definition: entryDefinition,
            }),
        });
        const responseBody = await parseJsonResponse(response) as SaveEntryResponse | null;

        if (!response.ok) {
            throw new Error(responseBody?.error ?? `Save failed with HTTP ${response.status}`);
        }
        if (responseBody === null) {
            throw new Error("Save response was empty");
        }

        saveResult = responseBody;
        saveState = "saved";
        compileResult = { dictionaries: [responseBody.compile] };
        compileState = "compiled";
    } catch (error) {
        saveState = "error";
        saveError = error instanceof Error ? error.message : String(error);
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

    <section class="entry-editor" aria-labelledby="entry-editor-title">
        <div class="section-heading">
            <div>
                <p class="eyebrow">Dictionary</p>
                <h2 id="entry-editor-title">Add entry</h2>
            </div>

            <button
                type="button"
                class="compile-button secondary compact"
                disabled={dictionaryLoadState === "loading"}
                onclick={() => loadDictionaries()}
            >
                {dictionaryLoadState === "loading" ? "Loading..." : "Reload dictionaries"}
            </button>
        </div>

        {#if dictionaryLoadState === "error"}
            <div class="entry-message is-error" aria-live="polite">{dictionaryLoadError}</div>
        {:else if dictionaryLoadState === "loaded" && dictionaries.length === 0}
            <div class="entry-message" aria-live="polite">No Hatchery dictionaries loaded</div>
        {/if}

        <form
            class="entry-form"
            onsubmit={(event) => {
                event.preventDefault();
                void saveEntry();
            }}
        >
            <label class="field">
                <span>Dictionary</span>
                <select
                    bind:value={selectedDictionaryPath}
                    disabled={dictionaryLoadState !== "loaded" || dictionaries.length === 0 || saveIsWorking}
                >
                    {#each dictionaries as dictionary}
                        <option value={dictionary.path}>{dictionaryLabel(dictionary)}</option>
                    {/each}
                </select>
            </label>

            <label class="field">
                <span>Translation</span>
                <input
                    type="text"
                    bind:value={entryTranslation}
                    disabled={saveIsWorking}
                    autocomplete="off"
                />
            </label>

            <label class="field full">
                <span>Definition</span>
                <textarea
                    bind:value={entryDefinition}
                    disabled={saveIsWorking}
                    rows="5"
                    spellcheck="false"
                ></textarea>
            </label>

            <div class="form-actions">
                <div class="selected-path" title={selectedDictionary?.path ?? ""}>
                    {selectedDictionary?.path ?? ""}
                </div>

                <button
                    type="submit"
                    class="compile-button"
                    disabled={!canSaveEntry}
                >
                    {saveIsWorking ? "Saving..." : "Save entry"}
                </button>
            </div>
        </form>

        {#if saveState === "saved" && saveResult !== null}
            <div class="entry-message is-success" aria-live="polite">
                <span>Saved {saveResult.entry.key}</span>
                <a href={breakdownHref(saveResult.entry.translation)}>Open breakdown</a>
            </div>
        {:else if saveState === "error"}
            <div class="entry-message is-error" aria-live="polite">{saveError}</div>
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

.topbar,
.section-heading,
.form-actions {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
}

.topbar {
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

h1,
h2 {
    margin: 0;
    font-weight: 750;
}

h1 {
    font-size: clamp(1.25rem, 2vw, 1.75rem);
}

h2 {
    font-size: 1.2rem;
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

.compile-button.compact {
    min-width: 0;
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

.status-strip,
.entry-message {
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

.status-strip.is-success,
.entry-message.is-success {
    background: #e7f5ec;
    color: #195e3d;
}

.status-strip.is-error,
.entry-message.is-error {
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

.entry-editor {
    display: grid;
    gap: 1rem;

    padding: 1.25rem clamp(1rem, 3vw, 2rem);
    border-bottom: 1px solid #d7ddd1;
    background: #ffffff;
}

.entry-form {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 1rem;
}

.field {
    display: grid;
    gap: 0.35rem;
    min-width: 0;

    color: #28342c;
    font-size: 0.9rem;
    font-weight: 700;
}

.field.full,
.form-actions {
    grid-column: 1 / -1;
}

input,
select,
textarea {
    width: 100%;
    min-width: 0;

    border: 1px solid #b9c2bb;
    border-radius: 4px;
    background: #ffffff;
    color: #17211b;
}

input,
select {
    height: 2.5rem;
    padding: 0 0.7rem;
}

textarea {
    min-height: 8.75rem;
    padding: 0.7rem;
    resize: vertical;

    font-family: "Atkinson Hyperlegible Mono", monospace;
    line-height: 1.45;
}

input:focus,
select:focus,
textarea:focus {
    border-color: #24825f;
    outline: 2px solid #b9decf;
    outline-offset: 1px;
}

.selected-path {
    min-width: 0;
    overflow: hidden;
    color: #526257;
    font-family: "Atkinson Hyperlegible Mono", monospace;
    font-size: 0.86rem;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.entry-message {
    justify-content: space-between;
    padding-inline: 0.85rem;
    border: 1px solid #d7ddd1;
    border-radius: 4px;
}

.entry-message a {
    color: currentColor;
    font-weight: 750;
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

@media (max-width: 680px) {
    .topbar,
    .section-heading,
    .form-actions {
        align-items: stretch;
        flex-direction: column;
    }

    .compile-button {
        width: 100%;
    }

    .actions {
        flex-direction: column;
    }

    .entry-form {
        grid-template-columns: 1fr;
    }

    .dictionary-result {
        grid-template-columns: 1fr;
        gap: 0.25rem;
    }
}
</style>
