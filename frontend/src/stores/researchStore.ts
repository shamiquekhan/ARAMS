import { create } from 'zustand';

interface ResearchState {
  currentTaskId: string | null;
  status: string;
  progress: any[];
  setTaskId: (id: string) => void;
  setStatus: (status: string) => void;
  addProgress: (event: any) => void;
  reset: () => void;
}

export const useResearchStore = create<ResearchState>((set) => ({
  currentTaskId: null,
  status: 'idle',
  progress: [],
  setTaskId: (id) => set({ currentTaskId: id }),
  setStatus: (status) => set({ status }),
  addProgress: (event) => set((state) => ({ progress: [...state.progress, event] })),
  reset: () => set({ currentTaskId: null, status: 'idle', progress: [] }),
}));
