package com.knowOcean.rag.user.controller;

import com.knowOcean.rag.auth.CurrentUserService;
import com.knowOcean.rag.common.api.ApiResponse;
import com.knowOcean.rag.common.log.OperationLog;
import com.knowOcean.rag.user.model.dto.ChangePasswordRequest;
import com.knowOcean.rag.user.service.AccountService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * 个人账户控制器，提供修改密码等接口。
 */
@OperationLog
@RestController
@RequestMapping("/api/account")
public class AccountController {

    private final AccountService accountService;
    private final CurrentUserService currentUserService;

    public AccountController(AccountService accountService, CurrentUserService currentUserService) {
        this.accountService = accountService;
        this.currentUserService = currentUserService;
    }

    /** 修改当前登录用户的密码 */
    @PostMapping("/change-password")
    public ApiResponse<Void> changePassword(@Valid @RequestBody ChangePasswordRequest request) {
        accountService.changePassword(currentUserService.getRequiredCurrentUser(), request);
        return ApiResponse.success(null);
    }
}
