import { base } from "$app/paths";
import type {
    CompileDictionaryResult,
    DictionarySummary,
} from "$lib/ploverApi";


export const dictionaryLabel = (
    dictionary: CompileDictionaryResult | DictionarySummary,
) => {
    if ("label" in dictionary && typeof dictionary.label === "string" && dictionary.label !== "") {
        return dictionary.label;
    }

    if (typeof dictionary.path === "string" && dictionary.path !== "") {
        return dictionary.path;
    }

    return "Hatchery dictionary";
};

export const dictionaryStatus = (dictionary: CompileDictionaryResult) => {
    if (typeof dictionary.status === "string" && dictionary.status !== "") {
        return dictionary.status.replaceAll("_", " ");
    }

    return "compiled";
};

export const breakdownHref = (translation: string) => (
    `${base}/translation/${encodeURIComponent(translation)}`
);

export const entryFormatLabel = (format: string) => {
    if (format === "sophemes") {
        return "Sophemes";
    }

    if (format === "theory-symbols") {
        return "Theory symbols";
    }

    return format;
};
