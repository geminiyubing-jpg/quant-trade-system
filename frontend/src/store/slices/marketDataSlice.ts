/**
 * ==============================================
 * 行情数据 Redux Slice
 * ==============================================
 */

import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface MarketQuote {
  symbol: string;
  name: string;
  price: number;
  change: number;
  change_pct: number;
  volume: number;
  amount: number;
  bid_price?: number;
  ask_price?: number;
  high?: number;
  low?: number;
  open?: number;
  prev_close?: number;
  timestamp: string;
}

interface MarketDataState {
  quotes: Record<string, MarketQuote>;
  loading: boolean;
  error: string | null;
  lastUpdate: string | null;
}

const initialState: MarketDataState = {
  quotes: {},
  loading: false,
  error: null,
  lastUpdate: null,
};

const marketDataSlice = createSlice({
  name: 'marketData',
  initialState,
  reducers: {
    updateQuote(state, action: PayloadAction<MarketQuote>) {
      const quote = action.payload;
      state.quotes[quote.symbol] = quote;
      state.lastUpdate = new Date().toISOString();
    },

    updateQuotes(state, action: PayloadAction<MarketQuote[]>) {
      action.payload.forEach((quote) => {
        state.quotes[quote.symbol] = quote;
      });
      state.lastUpdate = new Date().toISOString();
    },

    removeQuote(state, action: PayloadAction<string>) {
      const symbol = action.payload;
      delete state.quotes[symbol];
    },

    clearQuotes(state) {
      state.quotes = {};
      state.lastUpdate = null;
    },

    setLoading(state, action: PayloadAction<boolean>) {
      state.loading = action.payload;
    },

    setError(state, action: PayloadAction<string | null>) {
      state.error = action.payload;
    },

    clearError(state) {
      state.error = null;
    },
  },
});

export const { updateQuote, updateQuotes, removeQuote, clearQuotes, setLoading, setError, clearError } =
  marketDataSlice.actions;

export const marketDataActions = marketDataSlice.actions;

export default marketDataSlice.reducer;

// Selectors
export const selectQuotes = (state: { marketData: MarketDataState }) => state.marketData.quotes;

export const selectQuoteBySymbol = (symbol: string) => (state: { marketData: MarketDataState }) =>
  state.marketData.quotes[symbol];

export const selectMarketDataLoading = (state: { marketData: MarketDataState }) => state.marketData.loading;

export const selectMarketDataError = (state: { marketData: MarketDataState }) => state.marketData.error;
