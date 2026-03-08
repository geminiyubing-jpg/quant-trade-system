import { configureStore } from '@reduxjs/toolkit';

export const store = configureStore({
  reducer: {
    // 这里添加各个 slice reducer
    // auth: authReducer,
    // data: dataReducer,
    // strategy: strategyReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        // 忽略某些 action 的序列化检查
        ignoredActions: ['your/action/type'],
      },
    }),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
