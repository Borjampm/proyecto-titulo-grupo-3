/**
 * Hook personalizado para usar los servicios de API
 * 
 * Proporciona funciones de API con manejo de errores y loading states
 */

import { useState, useCallback } from 'react';
import { toast } from 'sonner@2.0.3';

export interface UseApiOptions {
  showSuccessToast?: boolean;
  showErrorToast?: boolean;
  successMessage?: string;
}

export interface ApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

export function useApi<T = any>() {
  const [state, setState] = useState<ApiState<T>>({
    data: null,
    loading: false,
    error: null,
  });

  const execute = useCallback(
    async (
      apiFunction: () => Promise<T>,
      options: UseApiOptions = {}
    ): Promise<T | null> => {
      const {
        showSuccessToast = false,
        showErrorToast = true,
        successMessage,
      } = options;

      setState({ data: null, loading: true, error: null });

      try {
        const result = await apiFunction();
        setState({ data: result, loading: false, error: null });

        if (showSuccessToast && successMessage) {
          toast.success(successMessage);
        }

        return result;
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Error desconocido';
        setState({ data: null, loading: false, error: errorMessage });

        if (showErrorToast) {
          toast.error(errorMessage);
        }

        return null;
      }
    },
    []
  );

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null });
  }, []);

  return {
    ...state,
    execute,
    reset,
  };
}

/**
 * Hook específico para operaciones de mutación (POST, PUT, DELETE)
 */
export function useMutation<TData = any, TVariables = any>() {
  const [state, setState] = useState<ApiState<TData>>({
    data: null,
    loading: false,
    error: null,
  });

  const mutate = useCallback(
    async (
      apiFunction: (variables: TVariables) => Promise<TData>,
      variables: TVariables,
      options: UseApiOptions = {}
    ): Promise<TData | null> => {
      const {
        showSuccessToast = true,
        showErrorToast = true,
        successMessage = 'Operación completada exitosamente',
      } = options;

      setState({ data: null, loading: true, error: null });

      try {
        const result = await apiFunction(variables);
        setState({ data: result, loading: false, error: null });

        if (showSuccessToast) {
          toast.success(successMessage);
        }

        return result;
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Error desconocido';
        setState({ data: null, loading: false, error: errorMessage });

        if (showErrorToast) {
          toast.error(errorMessage);
        }

        return null;
      }
    },
    []
  );

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null });
  }, []);

  return {
    ...state,
    mutate,
    reset,
  };
}

/**
 * Hook para queries con auto-fetch
 */
export function useQuery<T = any>(
  apiFunction: () => Promise<T>,
  dependencies: any[] = []
) {
  const [state, setState] = useState<ApiState<T>>({
    data: null,
    loading: true,
    error: null,
  });

  const refetch = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }));

    try {
      const result = await apiFunction();
      setState({ data: result, loading: false, error: null });
      return result;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Error desconocido';
      setState({ data: null, loading: false, error: errorMessage });
      toast.error(errorMessage);
      return null;
    }
  }, [apiFunction]);

  // Auto-fetch on mount and when dependencies change
  useState(() => {
    refetch();
  });

  return {
    ...state,
    refetch,
  };
}
