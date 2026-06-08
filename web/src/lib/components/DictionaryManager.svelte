<script lang="ts">
    import { base } from "$app/paths";
    import { onMount } from "svelte";
    import {
        compilePloverTheory,
        deletePloverEntry,
        loadPloverDictionaries,
        loadPloverDictionaryEntries,
        savePloverEntry,
        type CompileDictionaryResult,
        type CompileResponse,
        type DictionaryEntriesPagination,
        type DictionaryEntrySummary,
        type DictionaryStats,
        type DictionarySummary,
        type SaveEntryResponse,
    } from "$lib/ploverApi";

    type CompileState = "idle" | "compiling" | "compiled" | "error";
    type CompileAction = "compile" | "refresh";
    type PloverConnectionState = "checking" | "connected" | "error";
    type DictionaryLoadState = "loading" | "loaded" | "error";
    type EntryLoadState = "idle" | "loading" | "loaded" | "error";
    type SaveState = "idle" | "saving" | "saved" | "error";

    const ENTRY_PAGE_LIMIT = 100;

    let ploverConnectionState = $state<PloverConnectionState>("checking");
    let ploverConnectionError = $state<string | null>(null);

    let compileState = $state<CompileState>("idle");
    let compileAction = $state<CompileAction>("compile");
    let compileResult = $state<CompileResponse | null>(null);
    let compileError = $state<string | null>(null);

    let dictionaryLoadState = $state<DictionaryLoadState>("loading");
    let dictionaryLoadError = $state<string | null>(null);
    let dictionaries = $state<DictionarySummary[]>([]);
    let selectedDictionaryPath = $state("");

    let entryLoadState = $state<EntryLoadState>("idle");
    let entryLoadError = $state<string | null>(null);
    let dictionaryEntries = $state<DictionaryEntrySummary[]>([]);
    let dictionaryStats = $state<DictionaryStats | null>(null);
    let entryFilter = $state("");
    let entryQuery = $state("");
    let entryPageOffset = $state(0);
    let entryPagination = $state<DictionaryEntriesPagination | null>(null);
    let latestEntryRequestKey = "";

    let entryTranslation = $state("");
    let entryDefinition = $state("");
    let saveState = $state<SaveState>("idle");
    let saveError = $state<string | null>(null);
    let saveResult = $state<SaveEntryResponse | null>(null);
    let deletingEntryKey = $state<string | null>(null);
    let deleteError = $state<string | null>(null);

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
    const entryPageStart = $derived(
        entryPagination !== null && entryPagination.returnedCount > 0
            ? entryPagination.offset + 1
            : 0,
    );
    const entryPageEnd = $derived(
        entryPagination !== null
            ? entryPagination.offset + entryPagination.returnedCount
            : 0,
    );
    const entryTotalCount = $derived(entryPagination?.totalCount ?? 0);
    const entryHasPreviousPage = $derived(entryPagination?.hasPrevious ?? false);
    const entryHasNextPage = $derived(entryPagination?.hasNext ?? false);

    onMount(() => {
        void loadDictionaries();
    });

    $effect(() => {
        const dictionaryPath = selectedDictionaryPath;
        if (dictionaryLoadState !== "loaded" || dictionaryPath === "") {
            dictionaryEntries = [];
            dictionaryStats = null;
            entryPagination = null;
            entryLoadState = "idle";
            return;
        }

        void loadEntries(dictionaryPath, entryPageOffset, entryQuery);
    });

    const dictionaryLabel = (dictionary: CompileDictionaryResult | DictionarySummary) => {
        if ("label" in dictionary && typeof dictionary.label === "string" && dictionary.label !== "") {
            return dictionary.label;
        }

        if (typeof dictionary.path === "string" && dictionary.path !== "") {
            return dictionary.path;
        }

        return "Hatchery dictionary";
    };

    const dictionaryStatus = (dictionary: CompileDictionaryResult) => {
        if (typeof dictionary.status === "string" && dictionary.status !== "") {
            return dictionary.status.replaceAll("_", " ");
        }

        return "compiled";
    };

    const breakdownHref = (translation: string) => (
        `${base}/translation/${encodeURIComponent(translation)}`
    );

    const setConnectionError = (message: string) => {
        ploverConnectionState = "error";
        ploverConnectionError = message;
    };

    const setConnectionReady = () => {
        ploverConnectionState = "connected";
        ploverConnectionError = null;
    };

    const loadDictionaries = async () => {
        ploverConnectionState = "checking";
        ploverConnectionError = null;
        dictionaryLoadState = "loading";
        dictionaryLoadError = null;
        deleteError = null;

        try {
            const responseBody = await loadPloverDictionaries();
            dictionaries = responseBody.dictionaries;
            if (!dictionaries.some((dictionary) => dictionary.path === selectedDictionaryPath)) {
                selectedDictionaryPath = dictionaries[0]?.path ?? "";
            }
            setConnectionReady();
            dictionaryLoadState = "loaded";
        } catch (error) {
            const message = error instanceof Error ? error.message : String(error);
            dictionaries = [];
            selectedDictionaryPath = "";
            setConnectionError(message);
            dictionaryLoadState = "error";
            dictionaryLoadError = message;
        }
    };

    const loadEntries = async (
        dictionaryPath: string,
        offset: number,
        query: string,
    ) => {
        latestEntryRequestKey = `${dictionaryPath}\n${offset}\n${query}`;
        entryLoadState = "loading";
        entryLoadError = null;
        deleteError = null;

        try {
            const responseBody = await loadPloverDictionaryEntries(dictionaryPath, {
                offset,
                limit: ENTRY_PAGE_LIMIT,
                query,
            });
            if (latestEntryRequestKey !== `${dictionaryPath}\n${offset}\n${query}`) {
                return;
            }

            dictionaryEntries = responseBody.entries;
            dictionaryStats = responseBody.stats;
            entryPagination = responseBody.pagination;
            setConnectionReady();
            entryLoadState = "loaded";
        } catch (error) {
            if (latestEntryRequestKey !== `${dictionaryPath}\n${offset}\n${query}`) {
                return;
            }

            const message = error instanceof Error ? error.message : String(error);
            dictionaryEntries = [];
            dictionaryStats = null;
            entryPagination = null;
            setConnectionError(message);
            entryLoadState = "error";
            entryLoadError = message;
        }
    };

    const compileTheory = async (refreshCache = false) => {
        compileState = "compiling";
        compileAction = refreshCache ? "refresh" : "compile";
        compileResult = null;
        compileError = null;

        try {
            const responseBody = await compilePloverTheory(refreshCache);
            compileResult = responseBody;
            setConnectionReady();
            compileState = "compiled";
            if (selectedDictionaryPath !== "") {
                await loadEntries(selectedDictionaryPath, entryPageOffset, entryQuery);
            }
        } catch (error) {
            const message = error instanceof Error ? error.message : String(error);
            setConnectionError(message);
            compileState = "error";
            compileError = message;
        }
    };

    const saveEntry = async () => {
        if (!canSaveEntry) {
            return;
        }

        saveState = "saving";
        saveResult = null;
        saveError = null;
        deleteError = null;

        try {
            const responseBody = await savePloverEntry(
                selectedDictionaryPath,
                entryTranslation,
                entryDefinition,
            );
            saveResult = responseBody;
            saveState = "saved";
            compileResult = { dictionaries: [responseBody.compile] };
            setConnectionReady();
            compileState = "compiled";
            await loadEntries(selectedDictionaryPath, entryPageOffset, entryQuery);
        } catch (error) {
            const message = error instanceof Error ? error.message : String(error);
            setConnectionError(message);
            saveState = "error";
            saveError = message;
        }
    };

    const deleteEntry = async (entry: DictionaryEntrySummary) => {
        if (selectedDictionaryPath === "" || deletingEntryKey !== null) {
            return;
        }

        deletingEntryKey = entry.key;
        deleteError = null;

        try {
            const responseBody = await deletePloverEntry(selectedDictionaryPath, entry.key);
            compileResult = { dictionaries: [responseBody.compile] };
            setConnectionReady();
            compileState = "compiled";
            await loadEntries(selectedDictionaryPath, entryPageOffset, entryQuery);
        } catch (error) {
            const message = error instanceof Error ? error.message : String(error);
            setConnectionError(message);
            deleteError = message;
        } finally {
            deletingEntryKey = null;
        }
    };

    const selectDictionary = (dictionaryPath: string) => {
        selectedDictionaryPath = dictionaryPath;
        entryPageOffset = 0;
    };

    const applyEntryFilter = () => {
        entryQuery = entryFilter.trim();
        entryPageOffset = 0;
    };

    const previousEntryPage = () => {
        if (!entryHasPreviousPage) {
            return;
        }

        entryPageOffset = Math.max(0, entryPageOffset - ENTRY_PAGE_LIMIT);
    };

    const nextEntryPage = () => {
        if (!entryHasNextPage) {
            return;
        }

        entryPageOffset += ENTRY_PAGE_LIMIT;
    };
</script>

<section class="dictionary-page" aria-labelledby="dictionary-title">
    <header class="panel-header">
        <div>
            <p class="eyebrow">Dictionaries</p>
            <h1 id="dictionary-title">Loaded dictionaries</h1>
        </div>

        <button
            type="button"
            class="button secondary"
            disabled={dictionaryLoadState === "loading"}
            onclick={() => loadDictionaries()}
        >
            {dictionaryLoadState === "loading" ? "Loading" : "Reload"}
        </button>
    </header>

    <section
        class="status-strip"
        class:is-success={ploverConnectionState === "connected"}
        class:is-error={ploverConnectionState === "error"}
        aria-live="polite"
    >
        {#if ploverConnectionState === "checking"}
            <span class="spinner"></span>
            <span>Checking Plover connection</span>
        {:else if ploverConnectionState === "connected"}
            <span class="status-dot"></span>
            <span>Plover connection ready</span>
        {:else}
            <span class="status-dot"></span>
            <span>{ploverConnectionError ?? "Could not connect to Plover"}</span>
        {/if}
    </section>

    <div class="dictionary-layout">
        <aside class="dictionary-list" aria-label="Loaded dictionaries">
            {#if dictionaryLoadState === "error"}
                <div class="message is-error">{dictionaryLoadError}</div>
            {:else if dictionaryLoadState === "loaded" && dictionaries.length === 0}
                <div class="message">No Hatchery dictionaries loaded</div>
            {:else}
                {#each dictionaries as dictionary}
                    <button
                        type="button"
                        class="dictionary-option"
                        class:is-selected={dictionary.path === selectedDictionaryPath}
                        onclick={() => selectDictionary(dictionary.path)}
                    >
                        <span>{dictionary.label}</span>
                        <small title={dictionary.path}>{dictionary.path}</small>
                    </button>
                {/each}
            {/if}
        </aside>

        <div class="dictionary-detail">
            <section class="cache-panel" aria-labelledby="cache-title">
                <div>
                    <p class="eyebrow">Cache</p>
                    <h2 id="cache-title">Manual cache management</h2>
                </div>

                <div class="button-row">
                    <button
                        type="button"
                        class="button"
                        class:is-working={compileIsWorking && compileAction === "compile"}
                        disabled={compileIsWorking}
                        onclick={() => compileTheory(false)}
                    >
                        {compileIsWorking && compileAction === "compile" ? "Compiling" : "Compile"}
                    </button>

                    <button
                        type="button"
                        class="button secondary"
                        class:is-working={compileIsWorking && compileAction === "refresh"}
                        disabled={compileIsWorking}
                        onclick={() => compileTheory(true)}
                    >
                        {compileIsWorking && compileAction === "refresh" ? "Refreshing" : "Refresh cache"}
                    </button>
                </div>

                <div
                    class="message compact"
                    class:is-success={compileState === "compiled"}
                    class:is-error={compileState === "error"}
                    aria-live="polite"
                >
                    {#if compileState === "idle"}
                        Ready
                    {:else if compileState === "compiling"}
                        {compileAction === "refresh" ? "Refreshing cache" : "Compiling theory"}
                    {:else if compileState === "compiled"}
                        Compiled {compiledDictionaryCount} {compiledDictionaryCount === 1 ? "dictionary" : "dictionaries"}
                    {:else}
                        {compileError ?? "Compile failed"}
                    {/if}
                </div>
            </section>

            <section class="stats-panel" aria-label="Dictionary stats">
                <article>
                    <span>{dictionaries.length}</span>
                    <small>Loaded</small>
                </article>

                <article>
                    <span>{dictionaryStats?.entryCount ?? 0}</span>
                    <small>Entries</small>
                </article>

                <article>
                    <span>{dictionaryStats?.morphemeCount ?? 0}</span>
                    <small>Morphemes</small>
                </article>

                <article>
                    <span>{dictionaryStats?.definitionCount ?? 0}</span>
                    <small>Definitions</small>
                </article>
            </section>

            <section class="entry-editor" aria-labelledby="entry-editor-title">
                <div class="section-heading">
                    <div>
                        <p class="eyebrow">Entry</p>
                        <h2 id="entry-editor-title">Add entry</h2>
                    </div>

                    <div class="selected-path" title={selectedDictionary?.path ?? ""}>
                        {selectedDictionary?.label ?? ""}
                    </div>
                </div>

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
                            onchange={() => entryPageOffset = 0}
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
                        <button
                            type="submit"
                            class="button"
                            disabled={!canSaveEntry}
                        >
                            {saveIsWorking ? "Saving" : "Save entry"}
                        </button>
                    </div>
                </form>

                {#if saveState === "saved" && saveResult !== null}
                    <div class="message is-success" aria-live="polite">
                        <span>Saved {saveResult.entry.key}</span>
                        <a href={breakdownHref(saveResult.entry.translation)}>Open breakdown</a>
                    </div>
                {:else if saveState === "error"}
                    <div class="message is-error" aria-live="polite">{saveError}</div>
                {/if}
            </section>

            <section class="entries-panel" aria-labelledby="entries-title">
                <div class="section-heading">
                    <div>
                        <p class="eyebrow">Entries</p>
                        <h2 id="entries-title">Entry list</h2>
                    </div>

                    <form
                        class="filter-form"
                        onsubmit={(event) => {
                            event.preventDefault();
                            applyEntryFilter();
                        }}
                    >
                        <label class="filter-field">
                            <span>Filter key/definition</span>
                            <input
                                type="search"
                                bind:value={entryFilter}
                                autocomplete="off"
                            />
                        </label>

                        <button
                            type="submit"
                            class="button secondary compact"
                        >
                            Apply
                        </button>
                    </form>
                </div>

                {#if entryLoadState === "loading"}
                    <div class="message">Loading entries</div>
                {:else if entryLoadState === "error"}
                    <div class="message is-error">{entryLoadError}</div>
                {:else if selectedDictionaryPath === ""}
                    <div class="message">Select a dictionary</div>
                {:else if dictionaryEntries.length === 0}
                    <div class="message">No entries found</div>
                {:else}
                    <div class="entry-pagination" aria-live="polite">
                        <span>
                            Showing {entryPageStart}-{entryPageEnd} of {entryTotalCount}
                            {entryQuery === "" ? "" : ` matching "${entryQuery}"`}
                        </span>

                        <div class="button-row">
                            <button
                                type="button"
                                class="button secondary compact"
                                disabled={!entryHasPreviousPage}
                                onclick={previousEntryPage}
                            >
                                Previous
                            </button>

                            <button
                                type="button"
                                class="button secondary compact"
                                disabled={!entryHasNextPage}
                                onclick={nextEntryPage}
                            >
                                Next
                            </button>
                        </div>
                    </div>

                    <div class="entry-table" role="table" aria-label="Dictionary entries">
                        <div class="entry-row heading" role="row">
                            <span role="columnheader">Key</span>
                            <span role="columnheader">Translation</span>
                            <span role="columnheader">Definition</span>
                            <span role="columnheader">Action</span>
                        </div>

                        {#each dictionaryEntries as entry}
                            <div class="entry-row" role="row">
                                <span class="mono" role="cell">{entry.key}</span>
                                <span role="cell">{entry.translation ?? "Not resolved"}</span>
                                <span class="mono" role="cell">{entry.definition}</span>
                                <span role="cell">
                                    <button
                                        type="button"
                                        class="button danger compact"
                                        disabled={deletingEntryKey !== null}
                                        aria-label={`Delete ${entry.key}`}
                                        onclick={() => deleteEntry(entry)}
                                    >
                                        {deletingEntryKey === entry.key ? "Deleting" : "Delete"}
                                    </button>
                                </span>
                            </div>
                        {/each}
                    </div>
                {/if}

                {#if deleteError !== null}
                    <div class="message is-error" aria-live="polite">{deleteError}</div>
                {/if}
            </section>

            {#if compileResult !== null && compileResult.dictionaries.length > 0}
                <section class="compile-results" aria-label="Dictionary compile results">
                    {#each compileResult.dictionaries as dictionary}
                        <article>
                            <span title={dictionary.path}>{dictionaryLabel(dictionary)}</span>
                            <small>{dictionaryStatus(dictionary)}</small>
                        </article>
                    {/each}
                </section>
            {/if}
        </div>
    </div>
</section>

<style lang="scss">
    .dictionary-page {
        display: grid;
        gap: 1rem;

        min-width: 0;
    }

    .panel-header,
    .section-heading,
    .cache-panel,
    .form-actions,
    .button-row,
    .filter-form,
    .entry-pagination,
    .message {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }

    .panel-header,
    .section-heading,
    .cache-panel,
    .form-actions,
    .entry-pagination {
        justify-content: space-between;
    }

    .panel-header {
        min-height: 4.5rem;
    }

    .eyebrow,
    h1,
    h2 {
        margin: 0;
    }

    .eyebrow {
        color: oklch(0.42 0.035 170);
        font-size: 0.76rem;
        font-weight: 760;
        letter-spacing: 0;
        text-transform: uppercase;
    }

    h1 {
        color: oklch(0.2 0.028 160);
        font-size: 1.55rem;
        font-weight: 780;
    }

    h2 {
        color: oklch(0.24 0.028 160);
        font-size: 1.05rem;
        font-weight: 760;
    }

    .status-strip,
    .message {
        min-height: 2.5rem;
        padding: 0.6rem 0.75rem;
        border: 0.0625rem solid oklch(0.84 0.018 155);
        border-radius: 0.375rem;
        background: oklch(0.97 0.008 155);
        color: oklch(0.36 0.025 160);
        font-size: 0.92rem;
    }

    .status-strip.is-success,
    .message.is-success {
        border-color: oklch(0.82 0.08 155);
        background: oklch(0.96 0.035 155);
        color: oklch(0.34 0.11 155);
    }

    .status-strip.is-error,
    .message.is-error {
        border-color: oklch(0.82 0.08 28);
        background: oklch(0.97 0.035 28);
        color: oklch(0.42 0.13 28);
    }

    .message {
        justify-content: space-between;
    }

    .message.compact {
        min-height: 2.125rem;
        font-size: 0.86rem;
    }

    .message a {
        color: currentColor;
        font-weight: 760;
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
        border: 0.125rem solid currentColor;
        border-right-color: transparent;
        background: transparent;
        animation: spin 0.72s linear infinite;
    }

    .dictionary-layout {
        display: grid;
        grid-template-columns: minmax(14rem, 18rem) minmax(0, 1fr);
        gap: 1rem;

        min-width: 0;
    }

    .dictionary-list,
    .dictionary-detail,
    .cache-panel,
    .stats-panel,
    .entry-editor,
    .entries-panel,
    .compile-results {
        border: 0.0625rem solid oklch(0.84 0.016 155);
        border-radius: 0.5rem;
        background: oklch(0.995 0.002 160);
    }

    .dictionary-list {
        display: grid;
        align-content: start;
        gap: 0.5rem;

        min-width: 0;
        padding: 0.75rem;
    }

    .dictionary-option {
        display: grid;
        gap: 0.25rem;

        width: 100%;
        min-width: 0;
        min-height: 3.75rem;
        padding: 0.65rem 0.7rem;
        border: 0.0625rem solid transparent;
        border-radius: 0.375rem;
        background: transparent;
        color: oklch(0.24 0.028 160);
        cursor: pointer;
        text-align: left;
    }

    .dictionary-option:hover,
    .dictionary-option.is-selected {
        border-color: oklch(0.78 0.055 170);
        background: oklch(0.95 0.02 170);
    }

    .dictionary-option span,
    .dictionary-option small,
    .selected-path,
    .compile-results span {
        min-width: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .dictionary-option span {
        font-weight: 760;
    }

    .dictionary-option small,
    .selected-path,
    .compile-results small {
        color: oklch(0.45 0.024 165);
        font-family: "Atkinson Hyperlegible Mono", monospace;
        font-size: 0.78rem;
    }

    .dictionary-detail {
        display: grid;
        gap: 1rem;

        min-width: 0;
        padding: 1rem;
    }

    .cache-panel,
    .entry-editor,
    .entries-panel {
        display: grid;
        gap: 1rem;

        min-width: 0;
        padding: 1rem;
    }

    .cache-panel {
        grid-template-columns: minmax(0, 1fr) auto;
    }

    .cache-panel .message {
        grid-column: 1 / -1;
    }

    .button-row {
        flex-wrap: wrap;
        justify-content: flex-end;
    }

    .button {
        min-width: 7rem;
        min-height: 2.4rem;
        padding: 0 0.9rem;
        border: 0.0625rem solid oklch(0.48 0.11 160);
        border-radius: 0.375rem;
        background: oklch(0.5 0.12 160);
        color: oklch(0.99 0.002 160);
        cursor: pointer;
        font-weight: 760;
    }

    .button:hover:not(:disabled) {
        background: oklch(0.44 0.12 160);
    }

    .button.secondary {
        border-color: oklch(0.78 0.018 160);
        background: oklch(0.99 0.002 160);
        color: oklch(0.28 0.028 160);
    }

    .button.secondary:hover:not(:disabled) {
        background: oklch(0.95 0.012 160);
    }

    .button.danger {
        border-color: oklch(0.57 0.14 28);
        background: oklch(0.56 0.15 28);
    }

    .button.danger:hover:not(:disabled) {
        background: oklch(0.5 0.15 28);
    }

    .button.compact {
        min-width: 5.5rem;
        min-height: 2rem;
        padding-inline: 0.6rem;
        font-size: 0.84rem;
    }

    .button:disabled {
        cursor: wait;
        opacity: 0.65;
    }

    .stats-panel {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.75rem;

        min-width: 0;
        padding: 0.75rem;
    }

    .stats-panel article {
        display: grid;
        gap: 0.15rem;

        min-width: 0;
        padding: 0.75rem;
        border-radius: 0.375rem;
        background: oklch(0.96 0.018 200);
    }

    .stats-panel span {
        color: oklch(0.25 0.045 210);
        font-size: 1.35rem;
        font-weight: 790;
    }

    .stats-panel small {
        color: oklch(0.42 0.035 210);
        font-size: 0.78rem;
        font-weight: 730;
        text-transform: uppercase;
    }

    .entry-form {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 1rem;
    }

    .field,
    .filter-field {
        display: grid;
        gap: 0.35rem;

        min-width: 0;
        color: oklch(0.28 0.028 160);
        font-size: 0.9rem;
        font-weight: 730;
    }

    .field.full,
    .form-actions {
        grid-column: 1 / -1;
    }

    .filter-field {
        width: min(18rem, 100%);
    }

    .filter-form {
        width: min(26rem, 100%);
        justify-content: flex-end;
    }

    .filter-form .filter-field {
        flex: 1 1 14rem;
    }

    .entry-pagination {
        min-width: 0;
        min-height: 2.25rem;
        color: oklch(0.38 0.03 165);
        font-size: 0.88rem;
        font-weight: 730;
    }

    .entry-pagination span {
        min-width: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    input,
    select,
    textarea {
        width: 100%;
        min-width: 0;
        border: 0.0625rem solid oklch(0.76 0.018 160);
        border-radius: 0.375rem;
        background: oklch(1 0 0);
        color: oklch(0.2 0.028 160);
    }

    input,
    select {
        height: 2.4rem;
        padding: 0 0.7rem;
    }

    textarea {
        min-height: 8rem;
        padding: 0.7rem;
        resize: vertical;

        font-family: "Atkinson Hyperlegible Mono", monospace;
        line-height: 1.45;
    }

    input:focus,
    select:focus,
    textarea:focus {
        border-color: oklch(0.5 0.12 160);
        outline: 0.125rem solid oklch(0.86 0.075 160);
        outline-offset: 0.0625rem;
    }

    .entry-table {
        display: grid;

        min-width: 0;
        overflow: auto;
        border: 0.0625rem solid oklch(0.86 0.014 160);
        border-radius: 0.375rem;
    }

    .entry-row {
        display: grid;
        grid-template-columns: minmax(8rem, 0.7fr) minmax(8rem, 0.8fr) minmax(18rem, 1.8fr) minmax(5.5rem, auto);
        align-items: center;
        gap: 0.75rem;

        min-width: 48rem;
        min-height: 2.75rem;
        padding: 0.5rem 0.65rem;
        border-bottom: 0.0625rem solid oklch(0.9 0.01 160);
        color: oklch(0.24 0.028 160);
        font-size: 0.9rem;
    }

    .entry-row:last-child {
        border-bottom: 0;
    }

    .entry-row.heading {
        min-height: 2.3rem;
        background: oklch(0.96 0.012 160);
        color: oklch(0.36 0.025 160);
        font-size: 0.78rem;
        font-weight: 760;
        text-transform: uppercase;
    }

    .entry-row span {
        min-width: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .mono {
        font-family: "Atkinson Hyperlegible Mono", monospace;
    }

    .compile-results {
        display: grid;
        gap: 0.5rem;

        min-width: 0;
        padding: 0.75rem;
    }

    .compile-results article {
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto;
        align-items: center;
        gap: 0.75rem;

        min-width: 0;
        min-height: 2.25rem;
        padding: 0.5rem 0.65rem;
        border: 0.0625rem solid oklch(0.88 0.012 160);
        border-radius: 0.375rem;
    }

    .compile-results span {
        font-family: "Atkinson Hyperlegible Mono", monospace;
    }

    .compile-results small {
        text-transform: capitalize;
    }

    @keyframes spin {
        to {
            transform: rotate(1turn);
        }
    }

    @media (max-width: 58rem) {
        .dictionary-layout {
            grid-template-columns: 1fr;
        }

        .dictionary-list {
            grid-template-columns: repeat(auto-fit, minmax(12rem, 1fr));
        }

        .cache-panel {
            grid-template-columns: 1fr;
        }

        .button-row {
            justify-content: stretch;
        }

        .button-row .button,
        .panel-header .button {
            width: 100%;
        }
    }

    @media (max-width: 42rem) {
        .panel-header,
        .section-heading,
        .form-actions,
        .filter-form,
        .entry-pagination {
            align-items: stretch;
            flex-direction: column;
        }

        .stats-panel,
        .entry-form {
            grid-template-columns: 1fr;
        }

        .filter-field {
            width: 100%;
        }

        .filter-form {
            width: 100%;
        }

        .entry-pagination span {
            white-space: normal;
        }

        .message {
            align-items: flex-start;
            flex-direction: column;
        }
    }
</style>
