<script lang="ts">
    import { onMount } from "svelte";
    import CompileResults from "$lib/components/dictionary/CompileResults.svelte";
    import ConnectionStatusStrip from "$lib/components/dictionary/ConnectionStatusStrip.svelte";
    import DictionaryCachePanel from "$lib/components/dictionary/DictionaryCachePanel.svelte";
    import DictionarySidebar from "$lib/components/dictionary/DictionarySidebar.svelte";
    import DictionaryStatsPanel from "$lib/components/dictionary/DictionaryStatsPanel.svelte";
    import EntryListPanel from "$lib/components/dictionary/EntryListPanel.svelte";
    import {
        ENTRY_PAGE_LIMIT,
        type CompileAction,
        type CompileState,
        type DictionaryLoadState,
        type EntryLoadState,
        type PloverConnectionState,
        type SaveState,
    } from "$lib/components/dictionary/types";
    import {
        compilePloverTheory,
        deletePloverEntry,
        loadPloverDictionaries,
        loadPloverDictionaryEntries,
        savePloverEntry,
        type CompileResponse,
        type DictionaryEntriesPagination,
        type DictionaryEntrySummary,
        type DictionaryStats,
        type DictionarySummary,
        type SaveEntryResponse,
    } from "$lib/ploverApi";

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
                resolveTranslations: true,
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
            onclick={() => void loadDictionaries()}
        >
            {dictionaryLoadState === "loading" ? "Loading" : "Reload"}
        </button>
    </header>

    <ConnectionStatusStrip
        state={ploverConnectionState}
        error={ploverConnectionError}
    />

    <div class="dictionary-layout">
        <DictionarySidebar
            loadState={dictionaryLoadState}
            loadError={dictionaryLoadError}
            {dictionaries}
            {selectedDictionaryPath}
            onSelect={selectDictionary}
        />

        <div class="dictionary-detail">
            <DictionaryCachePanel
                {compileAction}
                {compileState}
                {compileError}
                {compiledDictionaryCount}
                {compileIsWorking}
                onCompile={compileTheory}
            />

            <DictionaryStatsPanel
                loadedCount={dictionaries.length}
                stats={dictionaryStats}
            />

            <EntryListPanel
                {entryLoadState}
                {entryLoadError}
                {selectedDictionaryPath}
                entries={dictionaryEntries}
                {entryFilter}
                {entryQuery}
                {entryPageStart}
                {entryPageEnd}
                {entryTotalCount}
                hasPreviousPage={entryHasPreviousPage}
                hasNextPage={entryHasNextPage}
                {entryTranslation}
                {entryDefinition}
                {saveState}
                {saveIsWorking}
                {canSaveEntry}
                {saveError}
                {saveResult}
                {deletingEntryKey}
                {deleteError}
                onFilterChange={(value) => entryFilter = value}
                onApplyFilter={applyEntryFilter}
                onPreviousPage={previousEntryPage}
                onNextPage={nextEntryPage}
                onTranslationChange={(value) => entryTranslation = value}
                onDefinitionChange={(value) => entryDefinition = value}
                onSave={saveEntry}
                onDeleteEntry={deleteEntry}
            />

            {#if compileResult !== null && compileResult.dictionaries.length > 0}
                <CompileResults dictionaries={compileResult.dictionaries} />
            {/if}
        </div>
    </div>
</section>

<style lang="scss">
    @use "./dictionary/dictionaryUi.scss" as ui;

    .dictionary-page {
        display: grid;
        gap: 1rem;

        min-width: 0;
    }

    .panel-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.75rem;

        min-height: 4.5rem;
    }

    .eyebrow {
        @include ui.eyebrow;
    }

    h1 {
        margin: 0;
        color: oklch(0.2 0.028 160);
        font-size: 1.55rem;
        font-weight: 780;
    }

    .button {
        @include ui.button;
        @include ui.secondary-button;
    }

    .dictionary-layout {
        display: grid;
        grid-template-columns: minmax(14rem, 18rem) minmax(0, 1fr);
        gap: 1rem;

        min-width: 0;
    }

    .dictionary-detail {
        display: grid;
        gap: 1rem;

        min-width: 0;
    }

    @media (max-width: 58rem) {
        .dictionary-layout {
            grid-template-columns: 1fr;
        }

        .panel-header .button {
            width: 100%;
        }
    }

    @media (max-width: 42rem) {
        .panel-header {
            align-items: stretch;
            flex-direction: column;
        }
    }
</style>
