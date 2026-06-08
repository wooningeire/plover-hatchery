<script lang="ts">
    import TranslationLookup from "$lib/components/TranslationLookup.svelte";

    type PageData = {
        translationText: string,
    };

    let {
        data,
    }: {
        data: PageData,
    } = $props();
</script>

<TranslationLookup
    initialTranslation={data.translationText}
    autoLookup={true}
/>
