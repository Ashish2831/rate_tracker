import { useEffect, useState } from "react";

/** Keeps selected provider in sync when latest rates first load. */
export function useDefaultProvider(providers: string[], initial = ""): [string, (value: string) => void] {
  const [selectedProvider, setSelectedProvider] = useState(initial);

  useEffect(() => {
    if (!selectedProvider && providers.length > 0) {
      setSelectedProvider(providers[0]);
    }
  }, [providers, selectedProvider]);

  return [selectedProvider, setSelectedProvider];
}
